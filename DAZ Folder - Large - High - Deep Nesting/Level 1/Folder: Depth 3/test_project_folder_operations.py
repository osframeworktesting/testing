import datetime
import logging
import os
import time
from urllib.parse import urlparse

import pytest

import markers
import settings
import utils
from api import osf_api
from pages.project import FilesPage


"""
*** NOTE ***
For the test user running this test, the following addons must be manually
authorized in user settings, or else the test will fail to run:
    - 'box', 'dropbox', 's3', 'owncloud'
"""

logger = logging.getLogger(__name__)

testable_addons = [
    'bitbucket',
    'box',
    'dataverse',
    'dropbox',
    'figshare',
    'github',
    'gitlab',
    's3',
    'onedrive',
    'owncloud',
]

skip_addons = [
    'bitbucket',
    'dataverse',
    'gitlab',
    'figshare',
    'owncloud',
    'github',
]


def find_folder_by_search(files_page, target_folder_name):
    # Search for target file
    files_page.search_input.clear()
    files_page.search_input.send_keys(target_folder_name)
    time.sleep(3)
    row = files_page.select_from_search_results(target_folder_name)
    return row


def connect_addon_to_node(driver, session, provider, node_id):
    """Use the api to connect a storage addon provider to a project node."""
    full_url = driver.current_url
    parsed_url = urlparse(full_url)
    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
    addon_account_id = osf_api.get_user_addon(session, provider, current_url=base_url)
    osf_api.connect_provider_root_to_node(
        session, provider, authorized_account_id=addon_account_id, node_id=node_id
    )


@markers.dont_run_on_prod
@pytest.mark.usefixtures('must_be_logged_in')
class TestFolderOperations:
    @pytest.mark.parametrize(
        'provider',
        [
            (
                pytest.param(
                    provider,
                    marks=pytest.mark.skip(reason='Functionality not supported'),
                )
                if provider in skip_addons
                else provider
            )
            for provider in testable_addons
        ]
        + ['osfstorage'],
    )
    def test_folder_creation(self, driver, default_project, session, provider):
        """Test that verifies create folder functionality for all storage addons and
        osfstorage.
        """
        current_browser = driver.desired_capabilities.get('browserName')
        node_id = default_project.id
        if provider != 'osfstorage':
            connect_addon_to_node(driver, session, provider, node_id)
        folder_name = 'Selenium ' + current_browser + ' ' + provider + ' Folder'
        try:
            # Navigate to files page
            files_page = FilesPage(driver, guid=node_id)
            files_page.goto()
            # Wait for File List items to load
            utils.wait_until_page_ready(driver)
            if provider != 'osfstorage':
                files_page.select_addon.click()
                files_page.select_from_addon_list(provider)
                utils.wait_until_page_ready(driver)
            # Click on create folder button
            files_page.click_on_button('Create Folder')
            utils.wait_until_page_ready(driver)
            files_page.create_folder_modal.enter_folder_name(folder_name)
            files_page.create_folder_modal.click_on_button('Create')
            utils.wait_until_page_ready(driver)
            # Test that new file name is present and visible
            new_folder = find_folder_by_search(files_page, folder_name)
            assert new_folder is not None

        finally:
            osf_api.delete_addon_folder(
                session, provider, guid=node_id, folder_name=folder_name
            )

    @pytest.mark.parametrize(
        'provider',
        [
            (
                pytest.param(
                    provider,
                    marks=pytest.mark.skip(reason='Functionality not supported'),
                )
                if provider in skip_addons
                else provider
            )
            for provider in testable_addons
        ]
        + ['osfstorage'],
    )
    def test_download_folder(self, driver, default_project, session, provider):
        """Test that verifies downloading folder via Download as zip button
        functionality for all storage addons and osfstorage.
        """
        current_browser = driver.desired_capabilities.get('browserName')
        node_id = default_project.id
        if provider != 'osfstorage':
            connect_addon_to_node(driver, session, provider, node_id)
        folder_name = 'download_' + current_browser + '_' + provider
        try:
            # Navigate to files page
            files_page = FilesPage(driver, guid=node_id)
            files_page.goto()
            # Wait for File List items to load
            utils.wait_until_page_ready(driver)
            if provider != 'osfstorage':
                files_page.select_addon.click()
                files_page.select_from_addon_list(provider)
                utils.wait_until_page_ready(driver)
            else:
                files_page.click_on_button('Create Folder')
                utils.wait_until_page_ready(driver)
                files_page.create_folder_modal.enter_folder_name(folder_name)
                files_page.create_folder_modal.click_on_button('Create')
                utils.wait_until_page_ready(driver)

            # Test that download folder name is present and visible
            row = find_folder_by_search(files_page, folder_name)
            files_page.click_on_folder_link(folder_name=folder_name, row=row)
            time.sleep(2)
            # Verify Folder Download Functionality
            files_page.click_on_button('Download As Zip')
            time.sleep(2)
            files_page.reload()
            if provider != 'osfstorage':
                files_page.select_addon.click()
                files_page.select_from_addon_list(provider)
                utils.wait_until_page_ready(driver)
            current_date = datetime.datetime.now()
            if settings.DRIVER == 'Remote':
                # First verify the downloaded file exists on the virtual remote machine
                assert driver.execute_script(
                    'browserstack_executor: {"action": "fileExists", "arguments": {"fileName": "%s"}}'
                    % (folder_name + '.zip')
                )
                # Next get the file properties and then verify that the file creation date is today
                file_props = driver.execute_script(
                    'browserstack_executor: {"action": "getFileProperties", "arguments": {"fileName": "%s"}}'
                    % (folder_name + '.zip')
                )
                file_create_date = datetime.datetime.fromtimestamp(
                    file_props['created_time']
                )
                assert file_create_date.date() == current_date.date()
            else:
                # First verify the downloaded file exists
                file_path = os.path.expanduser('~/Downloads/' + folder_name + '.zip')
                assert os.path.exists(file_path)
                # Next verify the folder was downloaded today
                file_mtime = os.path.getmtime(file_path)
                file_mod_date = datetime.datetime.fromtimestamp(file_mtime)
                assert file_mod_date.date() == current_date.date()
        except Exception:
            logger.error('Download error')

    @pytest.mark.parametrize(
        'provider',
        [
            (
                pytest.param(
                    provider,
                    marks=pytest.mark.skip(reason='Functionality not supported'),
                )
                if provider in skip_addons
                else provider
            )
            for provider in testable_addons
        ]
        + ['osfstorage'],
    )
    def test_rename_folder(self, driver, default_project, session, provider):
        """Test that verifies renaming folder via context menu button
        functionality for all storage addons and osfstorage.
        """
        current_browser = driver.desired_capabilities.get('browserName')
        node_id = default_project.id
        if provider != 'osfstorage':
            connect_addon_to_node(driver, session, provider, node_id)
        folder_name = 'rename_' + current_browser + '_' + provider
        try:
            # Navigate to files page
            files_page = FilesPage(driver, guid=node_id)
            files_page.goto()
            # Wait for File List items to load
            utils.wait_until_page_ready(driver)
            if provider != 'osfstorage':
                files_page.select_addon.click()
                files_page.select_from_addon_list(provider)
                utils.wait_until_page_ready(driver)

            # Click on create folder button
            files_page.click_on_button('Create Folder')
            utils.wait_until_page_ready(driver)
            files_page.create_folder_modal.enter_folder_name(folder_name)
            files_page.create_folder_modal.click_on_button('Create')
            utils.wait_until_page_ready(driver)

            # Test that new folder name is present and visible
            row = find_folder_by_search(files_page, folder_name)
            # Once we have found the right row we need to click the File Action menu
            # button at the far right side of the row to show the menu options. Then we
            # can click the Rename option from this menu.
            menu_button = row.find_element_by_xpath(
                '//button[@class="p-ripple p-button p-button-contrast p-button-icon-only p-button-raised p-button-sm p-button-text p-component"]'
            )
            menu_button.click()
            rename_button = row.find_element_by_xpath(
                '//a[@class="p-tieredmenu-item-link"]/span[text()="Rename"]'
            )
            rename_button.click()
            # Delete the old file name from the input box
            files_page.rename_file_modal.rename_input_box.clear()

            # Enter new file name in input box and click Save button
            new_name = current_browser + '_' + provider + '_renamed'
            files_page.rename_file_modal.rename_input_box.send_keys_deliberately(
                new_name
            )
            files_page.rename_file_modal.save_button.click()
            utils.wait_until_page_ready(driver)
            # Test old file name does not exist
            old_folder = find_folder_by_search(files_page, folder_name)
            assert old_folder is None
            # Test that new folder name is present and visible
            renamed_folder = find_folder_by_search(files_page, new_name)
            assert new_name in renamed_folder.text

        finally:
            osf_api.delete_addon_folder(
                session, provider, guid=node_id, folder_name=new_name
            )

    @pytest.mark.parametrize(
        'provider',
        [
            (
                pytest.param(
                    provider,
                    marks=pytest.mark.skip(reason='Functionality not supported'),
                )
                if provider
                in ('bitbucket', 'dataverse', 'figshare', 'github', 'gitlab')
                else provider
            )
            for provider in testable_addons
        ],
    )
    def test_move_folder(self, driver, default_project, session, provider):
        """Test that verifies move folder via context menu button
        functionality for all storage addons and osfstorage.
        """
        current_browser = driver.desired_capabilities.get('browserName')
        node_id = default_project.id
        if provider != 'osfstorage':
            connect_addon_to_node(driver, session, provider, node_id)
        folder_name = 'move_' + current_browser + '_' + provider
        try:
            # Navigate to files page
            files_page = FilesPage(driver, guid=node_id)
            files_page.goto()
            # Wait for File List items to load
            utils.wait_until_page_ready(driver)
            if provider != 'osfstorage':
                files_page.select_addon.click()
                files_page.select_from_addon_list(provider)
                utils.wait_until_page_ready(driver)
            # Click on create folder button
            files_page.click_on_button('Create Folder')
            utils.wait_until_page_ready(driver)
            files_page.create_folder_modal.enter_folder_name(folder_name)
            files_page.create_folder_modal.click_on_button('Create')
            utils.wait_until_page_ready(driver)
            # Test that new folder name is present and visible
            row = find_folder_by_search(files_page, folder_name)
            # Once we have found the right row we need to click the File Action menu
            # button at the far right side of the row to show the menu options. Then we
            # can click the Rename option from this menu.
            menu_button = row.find_element_by_xpath(
                '//button[@class="p-ripple p-button p-button-contrast p-button-icon-only p-button-raised p-button-sm p-button-text p-component"]'
            )
            menu_button.click()
            move_button = row.find_element_by_xpath(
                '//a[@class="p-tieredmenu-item-link"]/span[text()="Move"]'
            )
            driver.execute_script('window.scrollTo(0, document.body.scrollTop);')
            move_button.click()
            utils.wait_until_page_ready(driver)
            # Click the Project link on the Move modal to go up a level and then click
            # the OSF Storage link. Then click the Move button on the modal to move
            # the file to OSF Storage.
            # files_page.move_copy_modal.project_link.click()n
            files_page.move_copy_modal.provider_osfstorage_link.click()
            files_page.move_copy_modal.move_button.click()
            utils.wait_until_page_ready(driver)
            # After the move process has finished verify success toaster message on
            # the Files list page.
            # files_page.loading_indicator.here_then_gone()
            # We should still be on the page for the provider, so check that the file
            # is no longer listed here.
            moved_row = find_folder_by_search(files_page, folder_name)
            utils.wait_until_page_ready(driver)
            assert moved_row is None
            # Click the link in the left navbar to switch to OSF Storage and verify the
            # file has been moved there.
            driver.execute_script('window.scrollTo(0, document.body.scrollTop);')
            files_page.select_addon.click()
            files_page.select_from_addon_list('osfstorage')
            utils.wait_until_page_ready(driver)
            moved_row = find_folder_by_search(files_page, folder_name)
            utils.wait_until_page_ready(driver)
            assert folder_name in moved_row.text

        finally:
            osf_api.delete_addon_folder(
                session, provider, guid=node_id, folder_name=folder_name
            )

    @pytest.mark.parametrize(
        'provider',
        [
            (
                pytest.param(
                    provider,
                    marks=pytest.mark.skip(reason='Functionality not supported'),
                )
                if provider in skip_addons
                else provider
            )
            for provider in testable_addons
        ],
    )
    def test_copy_folder(self, driver, default_project, session, provider):
        """Test that verifies copy folder via context menu button
        functionality for all storage addons and osfstorage.
        """
        current_browser = driver.desired_capabilities.get('browserName')
        node_id = default_project.id
        if provider != 'osfstorage':
            connect_addon_to_node(driver, session, provider, node_id)
        folder_name = 'copy_' + current_browser + '_' + provider
        try:
            # Navigate to files page
            files_page = FilesPage(driver, guid=node_id)
            files_page.goto()
            # Wait for File List items to load
            utils.wait_until_page_ready(driver)
            if provider != 'osfstorage':
                files_page.select_addon.click()
                files_page.select_from_addon_list(provider)
                utils.wait_until_page_ready(driver)
            # Click on create folder button
            files_page.click_on_button('Create Folder')
            utils.wait_until_page_ready(driver)
            files_page.create_folder_modal.enter_folder_name(folder_name)
            files_page.create_folder_modal.click_on_button('Create')
            utils.wait_until_page_ready(driver)
            # Test that new folder name is present and visible
            row = find_folder_by_search(files_page, folder_name)
            # Once we have found the right row we need to click the File Action menu
            # button at the far right side of the row to show the menu options. Then we
            # can click the Rename option from this menu.
            menu_button = row.find_element_by_xpath(
                '//button[@class="p-ripple p-button p-button-contrast p-button-icon-only p-button-raised p-button-sm p-button-text p-component"]'
            )
            menu_button.click()
            copy_button = row.find_element_by_xpath(
                '//a[@class="p-tieredmenu-item-link"]/span[text()="Copy to"]'
            )
            driver.execute_script('window.scrollTo(0, document.body.scrollTop);')
            copy_button.click()
            utils.wait_until_page_ready(driver)
            # Click the Project link on the Move modal to go up a level and then click
            # the OSF Storage link. Then click the Move button on the modal to move
            # the file to OSF Storage.
            # files_page.move_copy_modal.project_link.click()n
            files_page.move_copy_modal.click_on_button('OSF Storage')
            files_page.move_copy_modal.copy_button.click()
            utils.wait_until_page_ready(driver)
            # After the move process has finished verify success toaster message on
            # the Files list page.
            # files_page.loading_indicator.here_then_gone()
            # We should still be on the page for the provider, so check that the file
            # is no longer listed here.
            source_row = find_folder_by_search(files_page, folder_name)
            assert folder_name in source_row.text
            # Click the link in the left navbar to switch to OSF Storage and verify the
            # file has been copied there.
            driver.execute_script('window.scrollTo(0, document.body.scrollTop);')
            files_page.select_addon.click()
            files_page.select_from_addon_list('osfstorage')
            utils.wait_until_page_ready(driver)
            files_page.loading_indicator.here_then_gone()
            destination_row = find_folder_by_search(files_page, folder_name)
            assert folder_name in destination_row.text

        finally:
            osf_api.delete_addon_folder(
                session, provider, guid=node_id, folder_name=folder_name
            )

    @pytest.mark.parametrize(
        'provider',
        [
            (
                pytest.param(
                    provider,
                    marks=pytest.mark.skip(reason='Functionality not supported'),
                )
                if provider in skip_addons
                else provider
            )
            for provider in testable_addons
        ]
        + ['osfstorage'],
    )
    def test_delete_folder(self, driver, default_project, session, provider):
        """Test that verifies delete folder via context menu button
        functionality for all storage addons and osfstorage.
        """
        current_browser = driver.desired_capabilities.get('browserName')
        node_id = default_project.id
        if provider != 'osfstorage':
            connect_addon_to_node(driver, session, provider, node_id)
        folder_name = 'delete_' + current_browser + '_' + provider
        try:
            # Navigate to files page
            files_page = FilesPage(driver, guid=node_id)
            files_page.goto()
            # Wait for File List items to load
            utils.wait_until_page_ready(driver)
            if provider != 'osfstorage':
                files_page.select_addon.click()
                files_page.select_from_addon_list(provider)
                utils.wait_until_page_ready(driver)
            # Click on create folder button
            files_page.click_on_button('Create Folder')
            utils.wait_until_page_ready(driver)
            files_page.create_folder_modal.enter_folder_name(folder_name)
            files_page.create_folder_modal.click_on_button('Create')
            utils.wait_until_page_ready(driver)
            # Test that new folder name is present and visible
            row = find_folder_by_search(files_page, folder_name)
            # Once we have found the right row we need to click the File Action menu
            # button at the far right side of the row to show the menu options. Then we
            # can click the Rename option from this menu.
            menu_button = row.find_element_by_xpath(
                '//button[@class="p-ripple p-button p-button-contrast p-button-icon-only p-button-raised p-button-sm p-button-text p-component"]'
            )
            menu_button.click()
            delete_button = row.find_element_by_xpath(
                '//a[@class="p-tieredmenu-item-link"]/span[text()="Delete"]'
            )
            delete_button.click()
            utils.wait_until_page_ready(driver)
            # Click the Delete button on the modal
            files_page.delete_modal.delete_button.click()
            # Verify file has been deleted from the files list
            deleted_row = find_folder_by_search(files_page, folder_name)
            assert deleted_row is None

        finally:
            osf_api.delete_addon_folder(
                session, provider, guid=node_id, folder_name=folder_name
            )


@markers.dont_run_on_prod
@pytest.mark.usefixtures('must_be_logged_in')
class TestFilesPageSort:
    @pytest.mark.parametrize(
        'provider',
        [
            (
                pytest.param(
                    provider,
                    marks=pytest.mark.skip(reason='Functionality not supported'),
                )
                if provider in ('bitbucket', 'dataverse', 'gitlab', 'owncloud')
                else provider
            )
            for provider in testable_addons
        ]
        + ['osfstorage'],
    )
    def test_sort_name_a_to_z(self, driver, default_project, session, provider):
        """Test to verify sorting by name from A to Z for given addon in
        project files page.
        """
        current_browser = driver.desired_capabilities.get('browserName')
        node_id = default_project.id
        if provider != 'osfstorage':
            connect_addon_to_node(driver, session, provider, node_id)
        node = osf_api.get_node(session, node_id=node_id)
        # Upload 3 separate test files to be moved
        file_name_1 = '1 AQA_' + current_browser + '_' + provider + '.txt'
        osf_api.delete_addon_file(
            session, provider, guid=node_id, file_name=file_name_1
        )
        new_file_1, metadata = osf_api.upload_fake_file(
            session=session, node=node, name=file_name_1, provider=provider
        )
        file_name_2 = 'ZZ AQA_' + current_browser + '_' + provider + '.txt'
        osf_api.delete_addon_file(
            session, provider, guid=node_id, file_name=file_name_2
        )
        new_file_2, metadata = osf_api.upload_fake_file(
            session=session, node=node, name=file_name_2, provider=provider
        )
        file_name_3 = '2 AQA_' + current_browser + '_' + provider + '.txt'
        osf_api.delete_addon_file(
            session, provider, guid=node_id, file_name=file_name_3
        )
        new_file_3, metadata = osf_api.upload_fake_file(
            session=session, node=node, name=file_name_3, provider=provider
        )

        try:
            # Navigate to files page
            files_page = FilesPage(driver, guid=node_id)
            files_page.goto()
            # Wait for File List items to load
            utils.wait_until_page_ready(driver)
            if provider != 'osfstorage':
                files_page.select_addon.click()
                files_page.select_from_addon_list(provider)
                utils.wait_until_page_ready(driver)
            files_page.select_sort_from_list('Name: A-Z')
            sorted_rows = driver.find_elements_by_xpath('//span[@class="entry-title"]')
            ui_list = [row.text.strip() for row in sorted_rows]
            expected_sorted_list = sorted(ui_list, key=str.lower)
            assert ui_list == expected_sorted_list
        finally:
            osf_api.delete_addon_files(session, provider, current_browser, guid=node_id)

    @pytest.mark.parametrize(
        'provider',
        [
            (
                pytest.param(
                    provider,
                    marks=pytest.mark.skip(reason='Functionality not supported'),
                )
                if provider in ('bitbucket', 'dataverse', 'gitlab', 'owncloud')
                else provider
            )
            for provider in testable_addons
        ]
        + ['osfstorage'],
    )
    def test_sort_name_z_to_a(self, driver, default_project, session, provider):
        """Test to verify sorting by name from Z to A for given addon in
        project files page.
        """
        current_browser = driver.desired_capabilities.get('browserName')
        node_id = default_project.id
        if provider != 'osfstorage':
            connect_addon_to_node(driver, session, provider, node_id)
        node = osf_api.get_node(session, node_id=node_id)
        # Upload 4 separate test files to be moved
        file_name_1 = '1 AQA_' + current_browser + '_' + provider + '.txt'
        osf_api.delete_addon_file(
            session, provider, guid=node_id, file_name=file_name_1
        )
        new_file_1, metadata = osf_api.upload_fake_file(
            session=session, node=node, name=file_name_1, provider=provider
        )
        file_name_2 = '2 AQA_' + current_browser + '_' + provider + '.txt'
        osf_api.delete_addon_file(
            session, provider, guid=node_id, file_name=file_name_2
        )
        new_file_2, metadata = osf_api.upload_fake_file(
            session=session, node=node, name=file_name_2, provider=provider
        )
        file_name_3 = 'ZZ AQA_' + current_browser + '_' + provider + '.txt'
        osf_api.delete_addon_file(
            session, provider, guid=node_id, file_name=file_name_3
        )
        new_file_3, metadata = osf_api.upload_fake_file(
            session=session, node=node, name=file_name_3, provider=provider
        )

        try:
            # Navigate to files page
            files_page = FilesPage(driver, guid=node_id)
            files_page.goto()
            # Wait for File List items to load
            utils.wait_until_page_ready(driver)
            if provider != 'osfstorage':
                files_page.select_addon.click()
                files_page.select_from_addon_list(provider)
                utils.wait_until_page_ready(driver)
            files_page.select_sort_from_list('Name: Z-A')
            sorted_rows = driver.find_elements_by_xpath('//span[@class="entry-title"]')
            ui_list = [row.text.strip() for row in sorted_rows]
            expected_sorted_list = sorted(ui_list, key=str.lower, reverse=True)
            assert ui_list == expected_sorted_list

        finally:
            osf_api.delete_addon_files(session, provider, current_browser, guid=node_id)

    @pytest.mark.parametrize(
        'provider',
        [
            (
                pytest.param(
                    provider,
                    marks=pytest.mark.skip(reason='Functionality not supported'),
                )
                if provider in ('bitbucket', 'dataverse', 'gitlab', 'owncloud')
                else provider
            )
            for provider in testable_addons
        ]
        + ['osfstorage'],
    )
    def test_sort_modified_date_descending(
        self, driver, default_project, session, provider
    ):
        """Test to verify sorting by name from A to Z for given addon in
        project files page.
        """
        current_browser = driver.desired_capabilities.get('browserName')
        node_id = default_project.id
        if provider != 'osfstorage':
            connect_addon_to_node(driver, session, provider, node_id)
        node = osf_api.get_node(session, node_id=node_id)
        # Upload 3 separate test files to be moved
        file_name_1 = 'Oldest AQA_' + current_browser + '_' + provider + '.txt'
        osf_api.delete_addon_file(
            session, provider, guid=node_id, file_name=file_name_1
        )
        new_file_1, metadata = osf_api.upload_fake_file(
            session=session, node=node, name=file_name_1, provider=provider
        )
        file_name_2 = 'Newest AQA_' + current_browser + '_' + provider + '.txt'
        osf_api.delete_addon_file(
            session, provider, guid=node_id, file_name=file_name_2
        )
        new_file_2, metadata = osf_api.upload_fake_file(
            session=session, node=node, name=file_name_2, provider=provider
        )

        try:
            # Navigate to files page
            files_page = FilesPage(driver, guid=node_id)
            files_page.goto()
            # Wait for File List items to load
            utils.wait_until_page_ready(driver)
            if provider != 'osfstorage':
                files_page.select_addon.click()
                files_page.select_from_addon_list(provider)
                utils.wait_until_page_ready(driver)
            files_page.select_sort_from_list('Last modified: oldest to newest')
            sorted_rows = driver.find_elements_by_xpath(
                '//div[@class="files-table-cell"][3]'
            )
            date_list = [row.text.strip() for row in sorted_rows]
            ui_dates = [
                datetime.strptime(item, '%b %d, %y %I:%M %p') for item in date_list
            ]
            assert ui_dates == sorted(ui_dates)
        finally:
            osf_api.delete_addon_files(session, provider, current_browser, guid=node_id)

    @pytest.mark.parametrize(
        'provider',
        [
            (
                pytest.param(
                    provider,
                    marks=pytest.mark.skip(reason='Functionality not supported'),
                )
                if provider in ('bitbucket', 'dataverse', 'gitlab', 'owncloud')
                else provider
            )
            for provider in testable_addons
        ]
        + ['osfstorage'],
    )
    def test_sort_modified_date_ascending(
        self, driver, default_project, session, provider
    ):
        """Test to verify sorting by name from A to Z for given addon in
        project files page.
        """
        current_browser = driver.desired_capabilities.get('browserName')
        node_id = default_project.id
        if provider != 'osfstorage':
            connect_addon_to_node(driver, session, provider, node_id)
        node = osf_api.get_node(session, node_id=node_id)
        # Upload 3 separate test files to be moved
        file_name_1 = 'Oldest AQA_' + current_browser + '_' + provider + '.txt'
        osf_api.delete_addon_file(
            session, provider, guid=node_id, file_name=file_name_1
        )
        new_file_1, metadata = osf_api.upload_fake_file(
            session=session, node=node, name=file_name_1, provider=provider
        )
        file_name_2 = 'Newest AQA_' + current_browser + '_' + provider + '.txt'
        osf_api.delete_addon_file(
            session, provider, guid=node_id, file_name=file_name_2
        )
        new_file_2, metadata = osf_api.upload_fake_file(
            session=session, node=node, name=file_name_2, provider=provider
        )

        try:
            # Navigate to files page
            files_page = FilesPage(driver, guid=node_id)
            files_page.goto()
            # Wait for File List items to load
            utils.wait_until_page_ready(driver)
            if provider != 'osfstorage':
                files_page.select_addon.click()
                files_page.select_from_addon_list(provider)
                utils.wait_until_page_ready(driver)
            files_page.select_sort_from_list('Last modified: newest to oldest')
            sorted_rows = driver.find_elements_by_xpath(
                '//div[@class="files-table-cell"][3]'
            )
            time.sleep(2)

            date_list = [row.text.strip() for row in sorted_rows]
            ui_dates = [
                datetime.strptime(item, '%b %d, %y %I:%M %p') for item in date_list
            ]
            assert ui_dates == sorted(ui_dates, reverse=True)
        finally:
            osf_api.delete_addon_files(session, provider, current_browser, guid=node_id)
