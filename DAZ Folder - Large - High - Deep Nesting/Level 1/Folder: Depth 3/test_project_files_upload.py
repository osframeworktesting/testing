import os
import shutil
import time
from urllib.parse import urlparse

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import markers
import settings
import utils
from api import osf_api
from pages.project import FilesPage


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
]


def find_file_by_search(files_page, target_file_name):
    # Search for target file
    files_page.search_input.clear()
    files_page.search_input.send_keys(target_file_name)
    time.sleep(2)
    row = files_page.select_from_search_results(target_file_name)
    return row


def find_files_by_search(files_page, target_string):
    # Search for target string
    time.sleep(2)
    files_page.search_input.clear()
    files_page.search_input.send_keys(target_string)
    time.sleep(2)
    rows = files_page.retrieve_search_results(target_string)
    return rows


def connect_addon_to_node(driver, session, provider, node_id):
    """Use the api to connect a storage addon provider to a project node."""
    full_url = driver.current_url
    parsed_url = urlparse(full_url)
    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
    addon_account_id = osf_api.get_user_addon(session, provider, current_url=base_url)
    osf_api.connect_provider_root_to_node(
        session, provider, authorized_account_id=addon_account_id, node_id=node_id
    )


def create_file_name_with_browser_provider(file_path, provider, browser):
    """Copy and Rename the file as given by the user in os path or project path"""
    base_dir = os.path.dirname(file_path)
    name, ext = os.path.splitext(os.path.basename(file_path))

    new_file_name = f'upload_{browser}_{provider}_{name}.txt'
    new_file_path = os.path.join(base_dir, new_file_name)
    shutil.copy(file_path, new_file_path)
    return new_file_path


@markers.dont_run_on_prod
@pytest.mark.usefixtures('must_be_logged_in')
class TestFilesUpload:
    """We want to wrap all of our tests with try/finally so we can delete leftover files
    after failures. Decorators did not work here because we would need to pull out
    node_id from each test.
    """

    def wait_until_page_ready(self, driver, timeout=30):
        wait = WebDriverWait(driver, timeout)

        wait.until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'p-progress-spinner'))
        )

    @pytest.mark.parametrize(
        'provider',
        [
            (
                pytest.param(
                    provider,
                    marks=pytest.mark.skip(reason='Functionality not supported'),
                )
                if provider in skip_addons + ['owncloud']
                else provider
            )
            for provider in testable_addons + ['osfstorage']
        ],
    )
    def test_upload_single_file(self, driver, default_project, session, provider):
        """Test to verify file upload to given storage addon.
        The addon is connected through api"""
        current_browser = driver.desired_capabilities.get('browserName')
        node_id = default_project.id
        if provider != 'osfstorage':
            connect_addon_to_node(driver, session, provider, node_id)

        # Upload a single test file
        original_file_name = 'selenium_test.txt'
        file_path = utils.get_test_file_path(original_file_name)
        file_name = (
            'upload_' + current_browser + '_' + provider + '_' + original_file_name
        )
        create_file_name_with_browser_provider(file_path, provider, current_browser)
        new_file_path = utils.get_test_file_path(file_name)
        # Delete file if already exists
        osf_api.delete_addon_file(session, provider, guid=node_id, file_name=file_name)
        try:
            files_page = FilesPage(driver, guid=node_id)
            files_page.goto()
            # Wait for File List items to load
            self.wait_until_page_ready(driver)
            if provider != 'osfstorage':
                files_page.select_addon.click()
                files_page.select_from_addon_list(provider)
            self.wait_until_page_ready(driver)
            files_page.click_on_button('Upload File')
            file_input = driver.find_element_by_css_selector('input[type="file"]')

            if settings.DRIVER == 'Remote':
                utils.upload_file_to_browserstack(new_file_path)
                file_input.send_keys(new_file_path)
            else:
                file_input.send_keys(new_file_path)

            files_page.reload()
            self.wait_until_page_ready(driver)
            # Verify that newly uploaded file exists in storage addon
            uploaded_file_row = find_file_by_search(files_page, file_name)
            assert uploaded_file_row is not None

        finally:
            os.remove(new_file_path)
            osf_api.delete_addon_files(session, provider, current_browser, guid=node_id)

    @pytest.mark.parametrize(
        'provider',
        [
            (
                pytest.param(
                    provider,
                    marks=pytest.mark.skip(reason='Functionality not supported'),
                )
                if provider in skip_addons + ['owncloud']
                else provider
            )
            for provider in testable_addons + ['osfstorage']
        ],
    )
    def test_upload_multiple_files(self, driver, default_project, session, provider):
        """Test to verify file upload to given storage addon."""

        current_browser = driver.desired_capabilities.get('browserName')
        node_id = default_project.id
        if provider != 'osfstorage':
            connect_addon_to_node(driver, session, provider, node_id)

        # Upload multiple test files at a time
        original_file_name1 = 'selenium_test1.txt'
        original_file_name2 = 'selenium_test2.txt'
        file_path1 = utils.get_test_file_path(original_file_name1)
        file_name1 = (
            'upload_' + current_browser + '_' + provider + '_' + original_file_name1
        )
        file_path2 = utils.get_test_file_path(original_file_name2)
        file_name2 = (
            'upload_' + current_browser + '_' + provider + '_' + original_file_name2
        )
        create_file_name_with_browser_provider(file_path1, provider, current_browser)
        create_file_name_with_browser_provider(file_path2, provider, current_browser)
        new_file_path1 = utils.get_test_file_path(file_name1)
        new_file_path2 = utils.get_test_file_path(file_name2)
        # Delete file if already exists
        osf_api.delete_addon_file(session, provider, guid=node_id, file_name=file_name1)
        osf_api.delete_addon_file(session, provider, guid=node_id, file_name=file_name2)
        try:
            files_page = FilesPage(driver, guid=node_id)
            files_page.goto()
            # Wait for File List items to load
            self.wait_until_page_ready(driver)
            if provider != 'osfstorage':
                files_page.select_addon.click()
                files_page.select_from_addon_list(provider)
            self.wait_until_page_ready(driver)
            files_page.click_on_button('Upload File')
            file_input = driver.find_element_by_css_selector('input[type="file"]')

            if settings.DRIVER == 'Remote':
                files = [new_file_path1, new_file_path2]
                for file in files:
                    utils.upload_file_to_browserstack(file)
                    file_input.send_keys(file)
                    time.sleep(3)
            else:
                files = [new_file_path1, new_file_path2]
                file_input.send_keys('\n'.join(files))

            files_page.reload()
            self.wait_until_page_ready(driver)
            # Verify that newly uploaded files exist in storage addon
            uploaded_file_rows = find_files_by_search(files_page, 'upload_')
            assert uploaded_file_rows is not None

        finally:
            os.remove(new_file_path1)
            os.remove(new_file_path2)
            osf_api.delete_addon_files(session, provider, current_browser, guid=node_id)
