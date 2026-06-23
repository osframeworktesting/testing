import logging
import time

import pytest
import requests
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import markers
import settings
import utils
from api import osf_api
from pages.project import (
    FilesMetadataPage,
    FilesPage,
    ProjectMetadataPage,
)
from pages.registries import RegistrationMetadataPage


logger = logging.getLogger(__name__)


def find_file_by_search(files_page, target_file_name):
    # Search for target file
    files_page.search_input.clear()
    files_page.search_input.send_keys(target_file_name)
    time.sleep(3)
    row = files_page.select_from_search_results(target_file_name)
    return row


@pytest.fixture()
def file_guid(driver, default_project, session, provider='osfstorage'):

    node_id = default_project.id
    node = osf_api.get_node(session, node_id=node_id)
    if settings.PREFERRED_NODE:
        new_file, metadata = osf_api.get_existing_file_data(session)
        files_page = FilesPage(driver, guid=settings.PREFERRED_NODE)
        files_page.goto()

        # Wait for File List items to load
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[@class='p-tree-root p-virtualscroller']")
            )
        )

        row = find_file_by_search(files_page, new_file)
        file_link = row.find_element_by_xpath(
            '//div[@class="flex align-items-center gap-2 hover:underline py-1 max-w-full"]'
        )
        file_link.click()
        driver.switch_to.window(driver.window_handles[0])
        file_id = metadata['data'][0]['attributes']['path']
        file_guid = osf_api.get_fake_file_guid(session, file_id)
        return file_guid

    else:
        try:
            new_file, metadata = osf_api.upload_fake_file(
                session=session,
                node=node,
                name='files_metadata_test.txt',
                provider=provider,
            )

            # files_page = FilesPage(driver, guid=node_id, addon_provider=provider)
            files_page = FilesPage(driver, guid=node_id)
            files_page.goto()
            if 'Not Found.' not in driver.page_source:
                # Wait for File List items to load
                WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located(
                        (By.XPATH, "//div[@class='p-tree-root p-virtualscroller']")
                    )
                )
                row = find_file_by_search(files_page, new_file)
                file_link = row.find_element_by_xpath(
                    '//div[@class="flex align-items-center gap-2 hover:underline py-1 max-w-full"]'
                )
                file_link.click()
                file_id = metadata['data']['attributes']['path']
                file_guid = osf_api.get_fake_file_guid(session, file_id)
                return file_guid
            else:
                raise Exception

        except Exception:
            logger.error('Server error occurred')
            osf_api.delete_addon_files(
                session, provider, current_browser=settings.DRIVER, guid=node_id
            )


@pytest.fixture()
def file_metadata_page(driver, session, file_guid):
    osf_api.update_file_metadata(session, file_guid)
    file_metadata_page = FilesMetadataPage(driver, guid=file_guid)
    file_metadata_page.goto()
    return file_metadata_page


def get_funder_information(funder_name):
    """This method is used to get the funder information for the
    given funder name using api link"""
    url = settings.FUNDER_INFO_URL
    response = requests.get(url)
    data = response.json()
    for funder in data['included']:
        if funder['type'] == 'index-card':
            if (
                funder['attributes']['resourceMetadata']['name'][0]['@value']
                == funder_name
            ):
                award_title = funder['attributes']['resourceMetadata']['resourceType'][
                    0
                ]['@id']
                award_uri = funder['attributes']['resourceIdentifier'][0]
                award_number = funder['id']

    return award_title, award_uri, award_number


# Below set of the tests will be fixed after fixing File funtcionality
@pytest.mark.usefixtures('must_be_logged_in')
@markers.dont_run_on_prod
@markers.core_functionality
class TestFilesMetadata:
    def test_edit_file_metadata(self, driver, file_metadata_page, fake):
        """This test verifies that the file metadata fields
        title, description, resource type and resource language
        are editable and changes are saved."""
        new_title = fake.sentence(nb_words=1)
        new_description = fake.sentence(nb_words=1)
        metadata_values_list = driver.find_elements_by_xpath(
            "//div[@class='flex flex-column gap-2']/p"
        )
        orig_title = metadata_values_list[0].text
        orig_description = metadata_values_list[1].text
        orig_resource_type = metadata_values_list[2].text
        orig_resource_language = metadata_values_list[3].text
        assert orig_title != new_title
        assert orig_description != new_description
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '//button[.//span[normalize-space()="Edit"]]',
                )
            )
        )
        driver.switch_to.window(driver.window_handles[0])
        file_metadata_page.files_metadata_edit_button.click()
        time.sleep(2)
        # Edit file metadata title
        file_metadata_page.edit_metadata_title_input.clear()
        file_metadata_page.edit_metadata_title_input.send_keys(new_title)
        # Edit file metadata title
        file_metadata_page.edit_metadata_description_input.clear()
        file_metadata_page.edit_metadata_description_input.send_keys(new_description)
        # Click on resource type dropdown and select given option
        resource_info_list = driver.find_elements_by_xpath(
            '//div[@aria-label="dropdown trigger"]'
        )
        resource_info_list[0].click()
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    'div.p-component.p-component-overlay.p-select-overlay> div > ul > p-selectitem > li > span',
                )
            )
        )
        file_metadata_page.select_from_dropdown_listbox('Collection')
        time.sleep(2)
        # Click on resource language dropdown and select given option
        resource_info_list[1].click()
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    'div.p-select-list-container > p-scroller > div > ul > p-selectitem > li > span',
                )
            )
        )
        file_metadata_page.select_by_search('Chinese')
        file_metadata_page.save_metadata_button.click()
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[@class='flex flex-column gap-2']/p")
            )
        )
        new_metadata_values_list = driver.find_elements_by_xpath(
            "//div[@class='flex flex-column gap-2']/p"
        )
        assert new_title == new_metadata_values_list[0].text
        assert new_description == new_metadata_values_list[1].text
        assert orig_resource_type != new_metadata_values_list[2].text
        assert orig_resource_language != new_metadata_values_list[3].text
        file_metadata_tab = utils.switch_to_new_tab(driver)
        utils.close_current_tab(driver, file_metadata_tab)

    def test_cancel_file_metadata_changes(self, driver, file_metadata_page, fake):
        """This test verifies the file metadata fields
        title, Description, Resource Type and Resource Language are editable
        and changes are cancelled without saving.
        """
        new_title = fake.sentence(nb_words=1)
        metadata_values_list = driver.find_elements_by_xpath(
            '//div[@class="flex flex-column gap-2"]/p'
        )
        orig_title = metadata_values_list[0].text
        assert orig_title != new_title
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '//button[.//span[normalize-space()="Edit"]]',
                )
            )
        )
        driver.switch_to.window(driver.window_handles[0])
        utils.wait_until_page_ready(driver)
        file_metadata_page.files_metadata_edit_button.click()
        utils.wait_until_page_ready(driver)
        # Edit file metadata title
        file_metadata_page.edit_metadata_title_input.clear()
        file_metadata_page.edit_metadata_title_input.send_keys(new_title)
        file_metadata_page.cancel_editing_button.click()
        new_metadata_values_list = driver.find_elements_by_xpath(
            '//div[@class="flex flex-column gap-2"]/p'
        )
        assert new_title != new_metadata_values_list[0].text
        file_metadata_tab = utils.switch_to_new_tab(driver)
        utils.close_current_tab(driver, file_metadata_tab)

    def test_download_file_metadata(self, driver, file_metadata_page):
        """This test verifies download functionality for file metadata."""

        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//button[@aria-label="Download"]',
                    )
                )
            ).click()
            if 'Not Found.' not in driver.page_source:
                file_metadata_page.reload()
                FilesMetadataPage(driver, verify=True)

                # Verify File Download Functionality
                if settings.DRIVER != 'Remote':
                    url = driver.find_element_by_xpath(
                        '//button[@aria-label="Download"]'
                    ).get_attribute('href')
                    guid = utils.get_guid_from_url(url, 3)
                    filename = utils.latest_download_file()
                    assert guid in filename
                else:
                    utils.verify_file_download(driver, file_name='')
            else:
                raise Exception

        except Exception:
            logger.error('404 Exception caught')
        if settings.env('TEST_BUILD') == 'edge':
            driver.close()
            remaining_window = driver.window_handles[0]
            driver.switch_to_window(remaining_window)
        else:
            file_metadata_tab = utils.switch_to_new_tab(driver)
            utils.close_current_tab(driver, file_metadata_tab)


@pytest.mark.usefixtures('must_be_logged_in')
@markers.dont_run_on_prod
@markers.core_functionality
class TestProjectMetadata:
    @pytest.fixture()
    def project_metadata_page(self, driver, default_project_with_metadata):
        project_metadata_page = ProjectMetadataPage(
            driver, guid=default_project_with_metadata.id
        )
        project_metadata_page.goto()
        return project_metadata_page

    @pytest.fixture()
    def project_metadata_page_with_contributors(
        self, driver, default_project_with_contributors
    ):
        project_metadata_page_with_contributors = ProjectMetadataPage(
            driver, guid=default_project_with_contributors.id
        )
        project_metadata_page_with_contributors.goto()
        return project_metadata_page_with_contributors

    @pytest.fixture()
    def project_metadata_page_with_affiliations(
        self, driver, default_project_with_affiliations
    ):
        project_metadata_page_with_affiliations = ProjectMetadataPage(
            driver, guid=default_project_with_affiliations.id
        )
        project_metadata_page_with_affiliations.goto()
        return project_metadata_page_with_affiliations

    @pytest.fixture()
    def project_metadata_page_with_subjects(
        self, driver, default_project_with_subjects
    ):
        project_metadata_page_with_subjects = ProjectMetadataPage(
            driver, guid=default_project_with_subjects.id
        )
        project_metadata_page_with_subjects.goto()
        return project_metadata_page_with_subjects

    @pytest.fixture()
    def project_metadata_page_with_license(
        self, driver, default_project_with_metadata_description_license
    ):
        project_metadata_page_with_license = ProjectMetadataPage(
            driver, guid=default_project_with_metadata_description_license.id
        )
        project_metadata_page_with_license.goto()
        return project_metadata_page_with_license

    @pytest.fixture()
    def project_metadata_page_with_tags(self, driver, default_project_with_tags):
        project_metadata_page_with_tags = ProjectMetadataPage(
            driver, guid=default_project_with_tags.id
        )
        project_metadata_page_with_tags.goto()
        return project_metadata_page_with_tags

    def test_edit_metadata_description(self, driver, project_metadata_page, fake):
        """This test verifies that the node level metadata field
        description is editable and changes are saved."""

        new_description = fake.sentence(nb_words=4)

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[h2[text()='Description']]//button[.='Edit']")
            )
        ).click()

        description_input = driver.find_element(By.ID, 'description')
        description_input.clear()
        description_input.send_keys(new_description)
        project_metadata_page.save_description_button.click()
        assert new_description == project_metadata_page.description.text.strip()

    def test_add_contributors(
        self, session, driver, project_metadata_page, default_project_with_metadata
    ):
        """This test verifies that user can add/remove
        contributors to project metadata."""

        if settings.DOMAIN == 'prod':
            new_user = 'OSF Tester1'
        else:
            new_user = 'OSF Runscope Admin'

        # Delete the user if its already exists
        osf_api.delete_project_contributor(
            session, node_id=default_project_with_metadata.id, user_name=new_user
        )
        project_metadata_page.click_on_edit('Contributors')
        project_metadata_page.click_add_contributor_button()
        project_metadata_page.add_contributor_search_input.click()
        project_metadata_page.add_contributor_search_input.send_keys(new_user)
        project_metadata_page.select_contributor_checkbox_by_name(new_user)
        project_metadata_page.click_on_button('Next')
        project_metadata_page.click_on_button('Done')
        # Check that modal window contains new user
        row_with_new_user = project_metadata_page.get_contributor_name_modal_window(
            new_user
        )
        assert row_with_new_user.text == new_user

        # Close modal window and check if 'Contributor' contains name of the new user
        project_metadata_page.click_on_button('Close')
        new_user_on_contributor_card = project_metadata_page.get_contributor_name(
            new_user
        )
        assert new_user_on_contributor_card.text == new_user

    def test_edit_contributor_permission(
        self, driver, session, project_metadata_page_with_contributors
    ):
        """This test verifies that user can update permissions for
        contributors on a  registration metadata."""

        contributor_name = 'OSF Runscope Admin'
        new_permission = 'Administrator'
        project_metadata_page_with_contributors.scroll_into_view(
            project_metadata_page_with_contributors.contributors_section.element
        )
        utils.wait_until_page_ready(driver)
        # Get contributors list for a registration
        contributors_list = (
            project_metadata_page_with_contributors.get_contributors_list()
        )
        # Verify that given contributor_name present in the list
        assert contributor_name in contributors_list
        # Edit contributors
        project_metadata_page_with_contributors.click_on_edit('Contributors')
        utils.wait_until_page_ready(driver)
        # Search for the contributor for which permissions need to be updated
        project_metadata_page_with_contributors.edit_contributors_modal.search_input.clear()
        project_metadata_page_with_contributors.edit_contributors_modal.search_input.send_keys(
            contributor_name
        )
        utils.wait_until_page_ready(driver)
        original_permission = (
            project_metadata_page_with_contributors.edit_contributors_modal.user_permission.text.strip()
        )
        assert original_permission != new_permission
        project_metadata_page_with_contributors.edit_contributors_modal.select_from_dropdown_listbox(
            new_permission
        )
        project_metadata_page_with_contributors.edit_contributors_modal.click_on_button(
            'Save'
        )
        utils.wait_until_page_ready(driver)
        permission_after_change = (
            project_metadata_page_with_contributors.edit_contributors_modal.user_permission.text.strip()
        )
        # Verify that user permissions are changed successfully
        assert permission_after_change == new_permission

    def test_edit_bibliographic_status_for_contributor(
        self, driver, session, project_metadata_page_with_contributors
    ):
        """This test verifies that user can edit bibliographic
        status for a contributor on a registration metadata."""

        contributor_name = 'OSF Runscope Admin'
        project_metadata_page_with_contributors.scroll_into_view(
            project_metadata_page_with_contributors.contributors_section.element
        )
        # Get contributors list for a registration
        contributors_list = (
            project_metadata_page_with_contributors.get_contributors_list()
        )
        # Verify that given contributor_name present in the list
        assert contributor_name in contributors_list
        project_metadata_page_with_contributors.click_on_edit('Contributors')
        utils.wait_until_page_ready(driver)
        # Search for the contributor for which status need to be updated
        project_metadata_page_with_contributors.edit_contributors_modal.search_input.clear()
        project_metadata_page_with_contributors.edit_contributors_modal.search_input.send_keys(
            contributor_name
        )
        project_metadata_page_with_contributors.edit_contributors_modal.click_on_bibliographic_checkbox()
        project_metadata_page_with_contributors.edit_contributors_modal.click_on_button(
            'Save'
        )
        project_metadata_page_with_contributors.edit_contributors_modal.click_on_button(
            'Close'
        )
        utils.wait_until_page_ready(driver)
        project_metadata_page_with_contributors.scroll_into_view(
            project_metadata_page_with_contributors.contributors_section.element
        )
        contributors_list = (
            project_metadata_page_with_contributors.get_contributors_list()
        )
        # Verify that user not shown in contributors list after bibliographic status is changed
        assert contributor_name not in contributors_list

    def test_remove_contributors(
        self, session, driver, project_metadata_page_with_contributors
    ):
        """This test verifies that user can remove
        contributors from project metadata."""

        if settings.DOMAIN == 'prod':
            new_user = 'OSF Tester1'
        else:
            new_user = 'OSF Runscope Admin'
        project_metadata_page_with_contributors.scroll_into_view(
            project_metadata_page_with_contributors.contributors_section.element
        )
        utils.wait_until_page_ready(driver)
        contributors_list = (
            project_metadata_page_with_contributors.get_contributors_list()
        )
        assert new_user in contributors_list
        project_metadata_page_with_contributors.goto_with_reload()
        utils.wait_until_page_ready(driver)
        project_metadata_page_with_contributors.click_on_edit('Contributors')
        project_metadata_page_with_contributors.edit_contributors_modal.search_input.clear()
        project_metadata_page_with_contributors.edit_contributors_modal.search_input.send_keys(
            new_user
        )
        project_metadata_page_with_contributors.edit_contributors_modal.remove_button.click()
        project_metadata_page_with_contributors.edit_contributors_modal.click_on_button(
            'Remove'
        )
        project_metadata_page_with_contributors.edit_contributors_modal.click_on_button(
            'Close'
        )

        # Check that modal window doesn't contains new user
        utils.wait_until_page_ready(driver)
        project_metadata_page_with_contributors.scroll_into_view(
            project_metadata_page_with_contributors.contributors_section.element
        )
        contributors_list = (
            project_metadata_page_with_contributors.get_contributors_list()
        )
        assert new_user not in contributors_list

    def test_edit_resource_information(self, driver, project_metadata_page):
        """This test verifies that user can add/remove
        resource information to project metadata."""
        orig_resource_type = project_metadata_page.resource_type.text
        orig_resource_language = project_metadata_page.resource_language.text

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[h2[text()=' Resource Information ']]//button[.='Edit']",
                )
            )
        ).click()

        # Select 'Book' from the resource type listbox
        project_metadata_page.resource_type_dropdown.click()
        driver.find_element(
            By.CSS_SELECTOR, 'li[role="option"][aria-label="Book"]'
        ).click()
        time.sleep(2)
        # project_metadata_page.select_from_dropdown_listbox('Book')
        # Select 'Bengali' from the resource language listbox
        project_metadata_page.resource_language_dropdown.click()
        project_metadata_page.select_by_search('Bengali')

        project_metadata_page.resource_information_save_button.click()
        assert orig_resource_type != project_metadata_page.resource_type.text
        assert orig_resource_language != project_metadata_page.resource_language.text

    def test_edit_support_funding_information(
        self, session, driver, project_metadata_page, default_project_with_metadata
    ):
        """This test verifies that user can add/remove
        funder information to project metadata."""

        funder_name = 'National Institutes of Health'
        # Get the funder information for the given funder name
        award_title, award_uri, award_number = get_funder_information(funder_name)
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[h2[text()='Funding/Support Information']]//button[.='Edit']",
                )
            )
        ).click()
        # Delete funder info if already exists
        funder_info = osf_api.get_funder_data_project(
            session, project_guid=default_project_with_metadata.id
        )
        if funder_info is not None:
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "(//span[normalize-space(text())='Remove'])[1]/ancestor::button",
                    )
                )
            ).click()
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[h2[text()='Funding/Support Information']]//button[.='Edit']",
                    )
                )
            ).click()

        project_metadata_page.funder_name.click()

        project_metadata_page.funder_name_search_input.send_keys(funder_name)
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, 'funderName-0_0'))
        ).click()
        project_metadata_page.award_title.click()
        project_metadata_page.award_title.send_keys(award_title)
        project_metadata_page.award_info_URI.click()
        project_metadata_page.award_info_URI.send_keys(award_uri)
        project_metadata_page.award_number.click()
        project_metadata_page.award_number.send_keys(award_number)
        project_metadata_page.add_funder_button.click()
        project_metadata_page.scroll_into_view(
            project_metadata_page.delete_funder_button.element
        )

        project_metadata_page.delete_funder_button.click()
        project_metadata_page.save_funder_info_button.click()

        assert funder_name in project_metadata_page.display_funder_name.text
        assert award_title in project_metadata_page.display_award_title.text
        assert award_number in project_metadata_page.display_award_number.text
        assert award_uri in project_metadata_page.dispaly_award_info_uri.text

    def test_add_affiliation(self, driver, session, project_metadata_page):
        """This test verifies that user can add
        affiliation to a registration metadata."""

        # Scroll to Affiliated Institution section
        project_metadata_page.scroll_into_view(
            project_metadata_page.affiliated_institutions.element
        )
        utils.wait_until_page_ready(driver)
        # Get the list of affiliations
        assert (
            project_metadata_page.affiliations_text.text.strip()
            == 'No affiliated institutions'
        )
        # Add new affiliation
        project_metadata_page.edit_affiliations_button.click()
        project_metadata_page.edit_affiliations_modal.select_all_button.click()
        project_metadata_page.edit_affiliations_modal.save_affiliations_button.click()
        project_metadata_page.reload()
        utils.wait_until_page_ready(driver)
        project_metadata_page.scroll_into_view(
            project_metadata_page.affiliated_institutions.element
        )
        utils.wait_until_page_ready(driver)
        new_affiliations_list = project_metadata_page.get_affiliations_list()
        assert len(new_affiliations_list) != 0

    def test_remove_affiliation(
        self, driver, session, project_metadata_page_with_affiliations
    ):
        """This test verifies that user can add
        affiliation to a registration metadata."""

        institution_id = 'google'
        # Scroll to Affiliated Institution section
        project_metadata_page_with_affiliations.scroll_into_view(
            project_metadata_page_with_affiliations.affiliated_institutions.element
        )
        utils.wait_until_page_ready(driver)
        # Get the list of affiliations
        affiliations_list = (
            project_metadata_page_with_affiliations.get_affiliations_list()
        )
        assert institution_id in affiliations_list
        # Add new affiliation
        project_metadata_page_with_affiliations.edit_affiliations_button.click()
        project_metadata_page_with_affiliations.edit_affiliations_modal.remove_all_button.click()
        project_metadata_page_with_affiliations.edit_affiliations_modal.save_affiliations_button.click()
        project_metadata_page_with_affiliations.reload()
        utils.wait_until_page_ready(driver)
        project_metadata_page_with_affiliations.scroll_into_view(
            project_metadata_page_with_affiliations.affiliated_institutions.element
        )
        utils.wait_until_page_ready(driver)
        assert (
            project_metadata_page_with_affiliations.affiliations_text.text.strip()
            == 'No affiliated institutions'
        )

    def test_add_top_level_subject(self, driver, session, project_metadata_page):
        """This test verifies that user can update
        subjects to a registration metadata."""
        new_top_level_subject = 'Business'
        project_metadata_page.scroll_into_view(project_metadata_page.subjects.element)
        utils.wait_until_page_ready(driver)
        subject_list = project_metadata_page.get_subject_list()
        assert new_top_level_subject not in subject_list
        project_metadata_page.select_top_level_subject(new_top_level_subject)
        project_metadata_page.reload()
        utils.wait_until_page_ready(driver)
        project_metadata_page.scroll_into_view(project_metadata_page.subjects.element)
        new_subject_list = project_metadata_page.get_subject_list()
        assert new_top_level_subject in new_subject_list

    def test_remove_top_level_subject(
        self, driver, session, project_metadata_page_with_subjects
    ):
        """This test verifies that user can update
        subjects to a registration metadata."""
        top_level_subject = 'Engineering'

        project_metadata_page_with_subjects.scroll_into_view(
            project_metadata_page_with_subjects.subjects.element
        )
        utils.wait_until_page_ready(driver)
        subject_list = project_metadata_page_with_subjects.get_subject_list()
        assert top_level_subject in subject_list
        project_metadata_page_with_subjects.remove_subject(top_level_subject)
        project_metadata_page_with_subjects.reload()
        utils.wait_until_page_ready(driver)
        project_metadata_page_with_subjects.scroll_into_view(
            project_metadata_page_with_subjects.subjects.element
        )
        utils.wait_until_page_ready(driver)
        new_subject_list = project_metadata_page_with_subjects.get_subject_list()
        assert top_level_subject not in new_subject_list

    def test_update_license(self, driver, session, project_metadata_page_with_license):
        """This test verifies that user can update
        license to a registration metadata."""
        license_info = project_metadata_page_with_license.license_info.text.strip()
        new_license = 'CC-By Attribution 4.0 International'
        assert license_info != new_license
        project_metadata_page_with_license.click_on_edit_license_button()
        utils.wait_until_page_ready(driver)
        project_metadata_page_with_license.edit_license_modal.select_from_dropdown_listbox(
            new_license
        )
        project_metadata_page_with_license.edit_license_modal.save_button.click()
        utils.wait_until_page_ready(driver)
        new_license_info = project_metadata_page_with_license.license_info.text.strip()
        assert new_license_info == new_license

    def test_add_tag(self, driver, session, project_metadata_page, fake):
        """This test verifies that user can add new
        tag to a registration metadata."""

        new_tag = fake.sentence(nb_words=4)
        project_metadata_page.scroll_into_view(
            project_metadata_page.tags_section.element
        )
        utils.wait_until_page_ready(driver)
        tags_list = project_metadata_page.get_tags_list()
        # Verify that new_tag is not in the list
        assert new_tag not in tags_list
        project_metadata_page.tag_input.clear()
        project_metadata_page.tag_input.send_keys(new_tag)
        actions = ActionChains(driver)
        actions.send_keys(Keys.ENTER).perform()
        utils.wait_until_page_ready(driver)
        new_tag_list = project_metadata_page.get_tags_list()
        # Verify that new_tag is in the list
        assert new_tag in new_tag_list

    def test_remove_tag(self, driver, session, project_metadata_page_with_tags):
        """This test verifies that user can remove
        tag from registration metadata."""

        new_tag = 'automation test'
        project_metadata_page_with_tags.scroll_into_view(
            project_metadata_page_with_tags.tags_section.element
        )
        utils.wait_until_page_ready(driver)
        tags_list = project_metadata_page_with_tags.get_tags_list()
        # Verify that new_tag is not in the list
        assert new_tag in tags_list
        project_metadata_page_with_tags.click_on_remove_tag(new_tag)
        utils.wait_until_page_ready(driver)
        new_tag_list = project_metadata_page_with_tags.get_tags_list()
        # Verify that new_tag is in the list
        assert new_tag not in new_tag_list


@pytest.mark.usefixtures('must_be_logged_in_as_registration_user')
@markers.dont_run_on_prod
@markers.core_functionality
class TestRegistrationMetadata:
    @pytest.fixture()
    def title(self):
        TITLE = 'Selenium Registration for Metadata tests'
        return TITLE

    @pytest.fixture()
    def registration_metadata_page(self, driver, title):
        registration_guid = osf_api.get_registration_by_title(title)

        if not registration_guid:
            raise ValueError(
                f"Registration with title '{title}' not found on the server."
            )

        osf_api.update_registration_metadata_with_custom_data(registration_guid)
        registration_metadata_page = RegistrationMetadataPage(
            driver, guid=registration_guid
        )
        registration_metadata_page.goto()
        return registration_metadata_page

    @pytest.fixture()
    def registration_guid(self, title):
        registration_guid = osf_api.get_registration_by_title(title)
        return registration_guid

    def test_edit_metadata_title_and_description(
        self, driver, registration_metadata_page, fake, registration_guid, title
    ):
        """This test verifies that the registration metadata title
        and description fields are editable and changes are saved."""

        new_title = 'Selenium Registration for Metadata tests'
        new_description = fake.sentence(nb_words=4)
        # original_title = 'Selenium Registration for Metadata tests'

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[h2[text()='Title']]//button[.='Edit']")
            )
        ).click()
        title_input = driver.find_element(
            By.XPATH, "//input[@placeholder='Edit title here']"
        )
        title_input.clear()
        title_input.send_keys(new_title)
        registration_metadata_page.save_metadata_title_button.click()
        assert new_title == utils.clean_text(
            registration_metadata_page.metadata_title.text
        )

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[h2[text()='Description']]//button[.='Edit']")
            )
        ).click()

        description_input = driver.find_element(By.ID, 'description')
        description_input.clear()
        description_input.send_keys(new_description)
        registration_metadata_page.save_metadata_description_button.click()
        assert new_description == utils.clean_text(
            registration_metadata_page.metadata_description.text.strip()
        )
        assert new_title == utils.clean_text(
            registration_metadata_page.metadata_title.text.strip()
        )
        osf_api.update_registration_title(
            registration_guid=registration_guid, title=title
        )

    def test_add_contributors(
        self, session, driver, registration_metadata_page, registration_guid
    ):
        """This test verifies that user can add/remove
        contributors to registration metadata."""

        if settings.DOMAIN == 'prod':
            new_user = 'OSF Tester1'
        else:
            new_user = 'OSF Runscope Admin'

        # Delete the user if its already exists
        osf_api.delete_registration_contributor(
            registration_guid=registration_guid, user_name=new_user
        )
        registration_metadata_page.goto_with_reload()
        registration_metadata_page.click_on_edit('Contributors')
        registration_metadata_page.click_add_contributor_button()
        registration_metadata_page.add_contributor_search_input.click()
        registration_metadata_page.add_contributor_search_input.send_keys(new_user)
        registration_metadata_page.select_contributor_checkbox_by_name(new_user)
        registration_metadata_page.click_on_button('Next')
        registration_metadata_page.click_on_button('Done')

        # Check that modal window contains new user
        row_with_new_user = (
            registration_metadata_page.get_contributor_name_modal_window(new_user)
        )
        assert row_with_new_user.text == new_user

        # Close modal window and check if 'Contributor' contains name of the new user
        registration_metadata_page.click_on_button('Close')
        new_user_on_contributor_card = registration_metadata_page.get_contributor_name(
            new_user
        )
        assert new_user_on_contributor_card.text == new_user

    def test_edit_contributor_permission(
        self, driver, session, registration_metadata_page
    ):
        """This test verifies that user can update permissions for
        contributors on a  registration metadata."""

        contributor_name = 'OSF Runscope Admin'
        new_permission = 'Administrator'
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.contributors_section.element
        )
        utils.wait_until_page_ready(driver)
        # Get contributors list for a registration
        contributors_list = registration_metadata_page.get_contributors_list()
        # Verify that given contributor_name present in the list
        assert contributor_name in contributors_list
        # Edit contributors
        registration_metadata_page.click_on_edit('Contributors')
        utils.wait_until_page_ready(driver)
        # Search for the contributor for which permissions need to be updated
        registration_metadata_page.edit_contributors_modal.search_input.clear()
        registration_metadata_page.edit_contributors_modal.search_input.send_keys(
            contributor_name
        )
        original_permission = (
            registration_metadata_page.edit_contributors_modal.user_permission.text.strip()
        )
        assert original_permission != new_permission
        registration_metadata_page.edit_contributors_modal.select_from_dropdown_listbox(
            new_permission
        )
        registration_metadata_page.edit_contributors_modal.click_on_button('Save')
        utils.wait_until_page_ready(driver)
        permission_after_change = (
            registration_metadata_page.edit_contributors_modal.user_permission.text.strip()
        )
        # Verify that user permissions are changed successfully
        assert permission_after_change == new_permission

    def test_edit_bibliographic_status_for_contributor(
        self, driver, session, registration_metadata_page
    ):
        """This test verifies that user can edit bibliographic
        status for a contributor on a registration metadata."""

        contributor_name = 'OSF Runscope Admin'
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.contributors_section.element
        )
        utils.wait_until_page_ready(driver)
        # Get contributors list for a registration
        contributors_list = registration_metadata_page.get_contributors_list()
        # Verify that given contributor_name present in the list
        assert contributor_name in contributors_list
        registration_metadata_page.click_on_edit('Contributors')
        utils.wait_until_page_ready(driver)
        # Search for the contributor for which status need to be updated
        registration_metadata_page.edit_contributors_modal.search_input.clear()
        registration_metadata_page.edit_contributors_modal.search_input.send_keys(
            contributor_name
        )
        registration_metadata_page.edit_contributors_modal.click_on_bibliographic_checkbox()
        registration_metadata_page.edit_contributors_modal.click_on_button('Save')
        registration_metadata_page.edit_contributors_modal.click_on_button('Close')
        utils.wait_until_page_ready(driver)
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.contributors_section.element
        )
        contributors_list = registration_metadata_page.get_contributors_list()
        # Verify that user not shown in contributors list after bibliographic status is changed
        assert contributor_name not in contributors_list

    def test_remove_contributors(
        self, session, driver, registration_metadata_page, registration_guid
    ):
        """This test verifies that user can add/remove
        contributors to registration metadata."""

        if settings.DOMAIN == 'prod':
            new_user = 'OSF Tester1'
        else:
            new_user = 'OSF Runscope Admin'
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.contributors_section.element
        )
        utils.wait_until_page_ready(driver)
        contributors_list = registration_metadata_page.get_contributors_list()
        # assert new_user in contributors_list
        registration_metadata_page.goto_with_reload()
        registration_metadata_page.click_on_edit('Contributors')
        registration_metadata_page.edit_contributors_modal.search_input.clear()
        registration_metadata_page.edit_contributors_modal.search_input.send_keys(
            new_user
        )
        registration_metadata_page.edit_contributors_modal.remove_button.click()
        registration_metadata_page.edit_contributors_modal.click_on_button('Remove')
        registration_metadata_page.edit_contributors_modal.click_on_button('Close')

        # Check that modal window doesn't contains new user
        utils.wait_until_page_ready(driver)
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.contributors_section.element
        )
        contributors_list = registration_metadata_page.get_contributors_list()
        assert new_user not in contributors_list

    def test_edit_resource_information(self, driver, registration_metadata_page):
        """This test verifies that user can add/remove
        resource information to registration metadata."""

        orig_resource_type = registration_metadata_page.resource_type.text
        orig_resource_language = registration_metadata_page.resource_language.text

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[h2[text()=' Resource Information ']]//button[.='Edit']",
                )
            )
        ).click()

        # Select 'Book' from the resource type listbox
        registration_metadata_page.resource_type_dropdown.click()
        driver.find_element(
            By.CSS_SELECTOR, 'li[role="option"][aria-label="Book"]'
        ).click()
        time.sleep(2)
        # project_metadata_page.select_from_dropdown_listbox('Book')
        # Select 'Bengali' from the resource language listbox
        registration_metadata_page.resource_language_dropdown.click()

        time.sleep(1)
        registration_metadata_page.select_by_search('Bengali')

        registration_metadata_page.resource_information_save_button.click()
        assert orig_resource_type != registration_metadata_page.resource_type.text
        assert (
            orig_resource_language != registration_metadata_page.resource_language.text
        )

    def test_edit_support_funding_information(
        self, driver, registration_metadata_page, session, registration_guid
    ):
        """This test verifies that user can add/remove
        funder information to registration metadata."""

        funder_name = 'National Institutes of Health'
        # Get funder information for the given funder name
        award_title, award_info_uri, award_number = get_funder_information(funder_name)

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[h2[text()='Funding/Support Information']]//button[.='Edit']",
                )
            )
        ).click()
        # Delete funder info if already exists
        funder_info = osf_api.get_funder_data_registration(registration_guid)
        if funder_info is not None:
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "(//span[normalize-space(text())='Remove'])[1]/ancestor::button",
                    )
                )
            ).click()
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[h2[text()='Funding/Support Information']]//button[.='Edit']",
                    )
                )
            ).click()

        registration_metadata_page.funder_name.click()

        registration_metadata_page.funder_name_search_input.send_keys(funder_name)
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'funderName-0_0'))
        ).click()
        registration_metadata_page.award_title.click()
        registration_metadata_page.award_title.send_keys(award_title)
        registration_metadata_page.award_info_URI.click()
        registration_metadata_page.award_info_URI.send_keys(award_info_uri)
        registration_metadata_page.award_number.click()
        registration_metadata_page.award_number.send_keys(award_number)
        registration_metadata_page.add_funder_button.click()
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.delete_funder_button.element
        )

        registration_metadata_page.delete_funder_button.click()
        registration_metadata_page.save_funder_info_button.click()

        assert funder_name in registration_metadata_page.display_funder_name.text
        assert award_title in registration_metadata_page.display_award_title.text
        assert award_number in registration_metadata_page.display_award_number.text
        assert award_info_uri in registration_metadata_page.dispaly_award_info_uri.text

    def test_add_affiliation(self, driver, session, registration_metadata_page):
        """This test verifies that user can add
        affiliation to a registration metadata."""

        institution_id = 'cos'
        # Scroll to Affiliated Institution section
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.affiliated_institutions.element
        )
        utils.wait_until_page_ready(driver)
        # Get the list of affiliations
        affiliations_list = registration_metadata_page.get_affiliations_list()
        assert institution_id not in affiliations_list
        # Add new affiliation
        registration_metadata_page.edit_affiliations_button.click()
        registration_metadata_page.edit_affiliations_modal.click_on_checkbox(
            institution_id
        )
        registration_metadata_page.edit_affiliations_modal.save_affiliations_button.click()
        registration_metadata_page.reload()
        utils.wait_until_page_ready(driver)
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.affiliated_institutions.element
        )
        utils.wait_until_page_ready(driver)
        new_affiliations_list = registration_metadata_page.get_affiliations_list()
        assert institution_id in new_affiliations_list

    def test_remove_affiliation(self, driver, session, registration_metadata_page):
        """This test verifies that user can add
        affiliation to a registration metadata."""

        institution_id = 'cos'
        # Scroll to Affiliated Institution section
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.affiliated_institutions.element
        )
        utils.wait_until_page_ready(driver)
        # Get the list of affiliations
        affiliations_list = registration_metadata_page.get_affiliations_list()
        assert institution_id in affiliations_list
        # Add new affiliation
        registration_metadata_page.edit_affiliations_button.click()
        registration_metadata_page.edit_affiliations_modal.click_on_checkbox(
            institution_id
        )
        registration_metadata_page.edit_affiliations_modal.save_affiliations_button.click()
        registration_metadata_page.reload()
        utils.wait_until_page_ready(driver)
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.affiliated_institutions.element
        )
        new_affiliations_list = registration_metadata_page.get_affiliations_list()
        assert institution_id not in new_affiliations_list

    def test_add_top_level_subject(self, driver, session, registration_metadata_page):
        """This test verifies that user can update
        subjects to a registration metadata."""
        new_top_level_subject = 'Business'
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.subjects.element
        )
        utils.wait_until_page_ready(driver)
        subject_list = registration_metadata_page.get_subject_list()
        assert new_top_level_subject not in subject_list
        registration_metadata_page.select_top_level_subject(new_top_level_subject)
        registration_metadata_page.reload()
        utils.wait_until_page_ready(driver)
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.subjects.element
        )
        utils.wait_until_page_ready(driver)
        new_subject_list = registration_metadata_page.get_subject_list()
        assert new_top_level_subject in new_subject_list

    def test_remove_top_level_subject(
        self, driver, session, registration_metadata_page
    ):
        """This test verifies that user can update
        subjects to a registration metadata."""
        top_level_subject = 'Business'
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.subjects.element
        )
        utils.wait_until_page_ready(driver)
        subject_list = registration_metadata_page.get_subject_list()
        assert top_level_subject in subject_list
        registration_metadata_page.remove_subject(top_level_subject)
        registration_metadata_page.reload()
        utils.wait_until_page_ready(driver)
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.subjects.element
        )
        new_subject_list = registration_metadata_page.get_subject_list()
        assert top_level_subject not in new_subject_list

    def test_update_license(self, driver, session, registration_metadata_page):
        """This test verifies that user can update
        license to a registration metadata."""
        # license_info = registration_metadata_page.license_info.text.strip()
        new_license = 'CC-By Attribution 4.0 International'
        registration_metadata_page.click_on_edit_license_button()
        utils.wait_until_page_ready(driver)
        registration_metadata_page.edit_license_modal.select_from_dropdown_listbox(
            new_license
        )
        registration_metadata_page.edit_license_modal.save_button.click()
        utils.wait_until_page_ready(driver)
        new_license_info = registration_metadata_page.license_info.text.strip()
        assert new_license_info == new_license

    def test_add_tag(self, driver, session, registration_metadata_page):
        """This test verifies that user can add new
        tag to a registration metadata."""

        new_tag = 'automation test'
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.tags_section.element
        )
        utils.wait_until_page_ready(driver)
        tags_list = registration_metadata_page.get_tags_list()
        # Verify that new_tag is not in the list
        assert new_tag not in tags_list
        registration_metadata_page.tag_input.clear()
        registration_metadata_page.tag_input.send_keys(new_tag)
        actions = ActionChains(driver)
        actions.send_keys(Keys.ENTER).perform()
        utils.wait_until_page_ready(driver)
        new_tag_list = registration_metadata_page.get_tags_list()
        # Verify that new_tag is in the list
        assert new_tag in new_tag_list

    def test_remove_tag(self, driver, session, registration_metadata_page):
        """This test verifies that user can remove
        tag from registration metadata."""

        new_tag = 'automation test'
        registration_metadata_page.scroll_into_view(
            registration_metadata_page.tags_section.element
        )
        utils.wait_until_page_ready(driver)
        tags_list = registration_metadata_page.get_tags_list()
        # Verify that new_tag is not in the list
        assert new_tag in tags_list
        registration_metadata_page.click_on_remove_tag(new_tag)
        utils.wait_until_page_ready(driver)
        new_tag_list = registration_metadata_page.get_tags_list()
        # Verify that new_tag is in the list
        assert new_tag not in new_tag_list
