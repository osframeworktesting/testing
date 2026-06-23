import datetime
import os
import time
import tkinter

import pytest
from pythosf import client
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import markers
import settings
from api import osf_api
from pages.registrations import MyRegistrationsPage
from pages.registries import (
    DraftRegistrationAnalysisPlanPage,
    DraftRegistrationDesignPlanPage,
    DraftRegistrationMetadataPage,
    DraftRegistrationOtherPage,
    DraftRegistrationReviewPage,
    DraftRegistrationSamplingPlanPage,
    DraftRegistrationStudyInfoPage,
    DraftRegistrationSummaryPage,
    DraftRegistrationVariablesPage,
    RegistrationAddNewPage,
    RegistrationDetailPage,
    RegistrationFileDetailPage,
    RegistrationFilesListPage,
    RegistrationTombstonePage,
    RegistriesDiscoverPage,
    RegistriesLandingPage,
)
from pages.search import SearchPage
from utils import find_current_browser


@pytest.fixture
def landing_page(driver):
    landing_page = RegistriesLandingPage(driver)
    landing_page.goto()
    return landing_page


def find_file_by_search(files_page, target_file_name):
    # Search for target file
    files_page.search_input.clear()
    files_page.search_input.send_keys(target_file_name)
    row = files_page.select_from_search_results(target_file_name)
    return row


class TestRegistriesSearch:
    @markers.two_minute_drill
    @markers.smoke_test
    @markers.core_functionality
    def test_search_results_exist(self, driver, landing_page):
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'registries_header'))
        ).click()
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'registries-overview'))
        ).click()
        landing_page.search_box.send_keys('QA Test')
        landing_page.search_box.send_keys(Keys.ENTER)
        # OSF Registries Discover page has been deprecated. So now searching from the
        # OSF Registries Landing page routes to the OSF Search page.
        search_page = SearchPage(driver, verify=True)
        search_page.loading_indicator.here_then_gone()
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
        )
        assert search_page.search_input.get_attribute('value') == 'QA Test'
        assert len(search_page.search_results) > 0
        assert search_page.first_card_object_type_label.text[:12] == 'Registration'

    @markers.smoke_test
    @markers.core_functionality
    def test_detail_page(self, driver):
        """Test a Registration Detail page by opening the first search result from the
        Registrations tab on the OSF Search page.
        """
        search_page = SearchPage(driver)
        search_page.goto()
        assert SearchPage(driver, verify=True)
        search_page.loading_indicator.here_then_gone()

        # Switch to the Registrations Tab
        search_page.registrations_tab_link.click()
        search_page.loading_indicator.here_then_gone()

        if not settings.PRODUCTION:
            # To avoid old registrations that may not have been properly converted to
            # new templates (especially in the staging environments) we want to sort the
            # results newest to oldest.
            search_page.sort_by_button.click()
            search_page.sort_by_date_created_newest.click()
            # Since all of the testing environments use the same SHARE server, we need
            # to enter a value in the search input box that will ensure that the results
            # are specific to the current environment.  We can do this by searching for
            # the test environment url in the identifiers metadata field.
            search_text = settings.OSF_HOME[8:]  # strip out "https://" from the url
        else:
            search_text = 'test'

        search_page.search_input.send_keys(search_text)
        search_page.search_input.send_keys(Keys.ENTER)
        search_page.loading_indicator.here_then_gone()
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
        )
        assert len(search_page.search_results) > 0

        # Skip any Withdrawn Registrations
        target_registration_link = driver.find_element(
            By.CSS_SELECTOR,
            'div.flex.align-items-center.gap-2 a.dark-blue-link.word-break-word',
        )
        target_registration_title = target_registration_link.text
        target_registration_link.click()

        # This is a hack. For some reason the new tab takes a couple of extra seconds
        # to open with Firefox and the number_of_windows_to_be expected condition
        # below isn't catching it.
        if 'firefox' in find_current_browser(driver):
            search_page.loading_indicator.here_then_gone()

        # Registration will open in a new tab
        try:
            # Wait for the new tab to open - window count should then = 2
            WebDriverWait(driver, 5).until(EC.number_of_windows_to_be(2))
            # Switch focus to the new tab
            driver.switch_to.window(driver.window_handles[1])
            detail_page = RegistrationDetailPage(driver, verify=True)
            assert detail_page.title.text in target_registration_title
        finally:
            # Close the second tab that was opened. We do not want subsequent tests to
            # use the second tab.
            driver.close()
            # Switch focus back to the first tab
            driver.switch_to.window(driver.window_handles[0])


@markers.smoke_test
@pytest.mark.usefixtures('throttle_on_prod')
@markers.core_functionality
class TestBrandedRegistriesPages:
    def providers():
        """Return all registration providers."""
        return osf_api.get_providers_list(type='registrations')

    @pytest.fixture(params=providers(), ids=[prov['id'] for prov in providers()])
    def provider(self, request):
        return request.param

    def test_discover_page(self, session, driver, provider):
        """This test will load the Discover page for each Branded Registry Provider that
        exists in an environment.
        """
        if provider['attributes']['branded_discovery_page']:
            discover_page = RegistriesDiscoverPage(driver, provider=provider)
            discover_page.goto()
            discover_page.loading_indicator.here_then_gone()
            assert RegistriesDiscoverPage(driver, verify=True)
            current_url = driver.current_url

            provider_id = provider['id'].lower()

            # Check if provider name in current url
            assert (
                provider_id in current_url.lower()
            ), f"Expected provider id '{provider_id}' to be in URL: {current_url}"
            assert 'registries/' in current_url


@markers.dont_run_on_prod
class TestDraftRegistration:
    @pytest.fixture
    def draft_registration(self, session, driver, default_project):
        """Return a draft registration created from a temporary project. This fixture
        uses the Open-Ended Registration schema in the OSF Registry. NOTE: Since the
        temporary project is deleted at the end of the test, this draft registration
        will also be automatically deleted.
        """

        # First get the schema id for an 'Open-Ended Registration'
        schema_list = osf_api.get_registration_schemas_for_provider(provider_id='osf')
        for schema in schema_list:
            if schema[0] == 'Open-Ended Registration':
                schema_id = schema[1]
                break

        return osf_api.create_draft_registration(
            session, node_id=default_project.id, schema_id=schema_id
        )

    def test_subjects_sort_order(self, driver, draft_registration, must_be_logged_in):
        """This test verifies that the list of Subjects on the Draft Registration
        Metadata page is sorted in alphabetical order.
        """

        # Navigate to the Draft Registration Metadata page
        metadata_page = DraftRegistrationMetadataPage(
            driver, draft_id=draft_registration['data']['id']
        )
        metadata_page.goto()
        assert DraftRegistrationMetadataPage(driver, verify=True)
        metadata_page.loading_indicator.here_then_gone()

        # Scroll down until the Subjects section is in view
        driver.execute_script(
            'arguments[0].scrollIntoView(true);',
            driver.find_element(By.XPATH, "//input[@aria-label='Tag input']"),
        )
        time.sleep(1)

        # Create a list of the top level subject names as they are displayed on the page
        subject_list = [subject.text for subject in metadata_page.top_level_subjects]

        # Create a sorted copy of the subject list
        sorted_subjects = sorted(subject_list.copy())

        # Verify that the sorted list matches the original subject list indicating that
        # the subject list as displayed on the page is correctly sorted alphabetically.
        assert sorted_subjects == subject_list

        # Expand the first top level subject to show the list of secondary subjects
        metadata_page.expand_first_subject_button.click()
        metadata_page.loading_indicator.here_then_gone()

        # Create a list of the expanded second level subject names and a sorted copy
        # of the list and verify that the second level subject list is also sorted
        # correctly.
        sec_subject_list = [
            subject.text
            for subject in metadata_page.first_subject_second_level_subjects
        ]
        sec_sorted_subjects = sorted(sec_subject_list.copy())
        assert sec_sorted_subjects == sec_subject_list


@markers.dont_run_on_prod
class TestRegistrationSubmission:
    @pytest.fixture
    def registration_user_session(self):
        return client.Session(
            api_base_url=settings.API_DOMAIN,
            auth=(settings.REGISTRATIONS_USER, settings.REGISTRATIONS_USER_PASSWORD),
        )

    @pytest.fixture
    def project_with_file_reg(self, registration_user_session):
        """Returns a project with a file using the login session of the Registrations
        User.
        """
        project = osf_api.create_project(
            registration_user_session, title='OSF Registration Project'
        )
        osf_api.upload_fake_file(
            registration_user_session,
            project,
            name='osf selenium test file for registration.txt',
        )
        yield project
        project.delete()

    @pytest.fixture
    def add_new_page(self, driver, login_as_user_with_registrations):
        """Navigate to the Add New Registration page"""
        add_new_page = RegistrationAddNewPage(driver)
        time.sleep(2)
        add_new_page.goto()
        assert RegistrationAddNewPage(driver, verify=True)
        return add_new_page

    @pytest.mark.skip(reason='Schema are different on different environments')
    def test_submit_registration_from_project(
        self, driver, project_with_file_reg, add_new_page
    ):
        """This test creates a new draft registration from a project with a file
        attached starting from the Add New Registration page.  The test uses the OSF
        Preregistration schema template and enters data in all of the required template
        fields while leaving most of the other data fields empty. The completed draft
        registration is submitted and made public immediately (not embargoed). The
        associated project is then deleted as cleanup. The registration is permanent
        and cannot be deleted.
        """

        # Click the Yes has project radio button and verify that the Project listbox is
        # then displayed
        driver.execute_script(
            'arguments[0].scrollIntoView(true);',
            driver.find_element(
                By.XPATH, "//button[.//span[normalize-space(text())='Yes']]"
            ),
        )
        add_new_page.has_project_button.click()
        assert add_new_page.project_listbox_trigger.present()

        # Select the dummy project name from the listbox
        add_new_page.project_listbox_trigger.click()
        WebDriverWait(driver, 5).until(
            EC.text_to_be_present_in_element(
                (
                    By.CSS_SELECTOR,
                    'li[role="option"].p-select-option',
                ),
                'OSF Registration Project',
            )
        )
        add_new_page.select_from_dropdown_listbox('OSF Registration Project')

        # Select 'OSF Preregistration' from the Schema listbox
        add_new_page.scroll_into_view(add_new_page.schema_listbox_trigger.element)
        add_new_page.schema_listbox_trigger.click()

        add_new_page.select_from_dropdown_listbox('OSF Preregistration')

        # Click the Create draft button and verify that we are navigated to the Draft
        # Registration Metadata page
        driver.execute_script(
            'arguments[0].scrollIntoView(true);',
            driver.find_element(By.XPATH, "//button[.//span[text()='Create draft']]"),
        )
        add_new_page.create_draft_button.click()
        metadata_page = DraftRegistrationMetadataPage(driver, verify=True)

        # Enter data in the input fields on the Draft Metadata page
        metadata_page.title_input.clear()
        metadata_page.title_input.send_keys(
            'Selenium Test Project With File Registration'
        )

        metadata_page.description_textarea.click()
        metadata_page.description_textarea.send_keys(
            'This is a test registration created from a project using Selenium.'
        )

        metadata_page.license_listbox_trigger.click()

        metadata_page.select_from_dropdown_listbox('CC0 1.0 Universal')

        metadata_page.scroll_into_view(metadata_page.tags_input_box.element)
        metadata_page.select_top_level_subject('Engineering')
        WebDriverWait(driver, 5).until(
            EC.visibility_of(metadata_page.first_selected_subject)
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });",
            driver.find_element(By.CSS_SELECTOR, 'p-chip.p-chip'),
        )
        assert metadata_page.first_selected_subject.text == 'Engineering'

        metadata_page.tags_input_box.click()
        metadata_page.tags_input_box.send_keys('selenium\r')

        metadata_page.scroll_into_view(metadata_page.next_page_button.element)
        footer = driver.find_element(By.CSS_SELECTOR, 'osf-footer')
        driver.execute_script(
            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });", footer
        )
        metadata_page.next_page_button.click()

        # NOTE: On the following draft pages we are only going to enter data in the
        # required fields.

        # Study Information Page
        study_page = DraftRegistrationStudyInfoPage(driver, verify=True)
        assert study_page.page_heading.text == 'Study Information'

        study_page.hypothesis_textbox.click()
        study_page.hypothesis_textbox.send_keys(
            'Hypothesis textbox - regression testing using selenium.'
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });", footer
        )
        study_page.next_page_button.click()

        # Design Plan Page
        design_page = DraftRegistrationDesignPlanPage(driver, verify=True)
        assert design_page.page_heading.text == 'Design Plan'

        design_page.other_radio_button.click()
        design_page.no_blinding_checkbox.click()
        design_page.scroll_into_view(design_page.study_design_textbox.element)
        design_page.study_design_textbox.click()
        design_page.study_design_textbox.send_keys(
            'Study Design textbox - regression testing using selenium.'
        )

        design_page.scroll_into_view(design_page.next_page_button.element)
        driver.execute_script(
            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });", footer
        )
        design_page.next_page_button.click()

        # Sampling Plan Page
        sampling_page = DraftRegistrationSamplingPlanPage(driver, verify=True)
        assert sampling_page.page_heading.text == 'Sampling Plan'

        sampling_page.reg_following_radio_button.click()
        sampling_page.scroll_into_view(sampling_page.data_procedures_textbox.element)
        sampling_page.data_procedures_textbox.click()
        sampling_page.data_procedures_textbox.send_keys(
            'Data Collection Procedures textbox - regression testing using selenium.'
        )

        # Purposely leave Sample Size textbox empty even though it is required

        sampling_page.scroll_into_view(sampling_page.next_page_button.element)
        driver.execute_script(
            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });", footer
        )
        sampling_page.next_page_button.click()

        # Variables Page
        variables_page = DraftRegistrationVariablesPage(driver, verify=True)
        assert variables_page.page_heading.text == 'Variables'

        # Verify that the Required Data Missing Indicator now displays in the left
        # sidebar since we left a required textbox empty on the previous page.
        variables_page.missing_data_ind.present()

        variables_page.scroll_into_view(variables_page.next_page_button.element)
        driver.execute_script(
            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });", footer
        )
        variables_page.next_page_button.click()

        # Analysis Plan Page
        analysis_page = DraftRegistrationAnalysisPlanPage(driver, verify=True)
        assert analysis_page.page_heading.text == 'Analysis Plan'

        analysis_page.stat_models_textbox.click()
        analysis_page.stat_models_textbox.send_keys(
            'Statistical Models textbox - regression testing using selenium.'
        )

        analysis_page.scroll_into_view(analysis_page.next_page_button.element)
        driver.execute_script(
            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });", footer
        )
        time.sleep(1)
        analysis_page.next_page_button.click()

        # Other Page
        other_page = DraftRegistrationOtherPage(driver, verify=True)
        assert other_page.page_heading.text == 'Other'

        other_page.other_textbox.click()
        other_page.other_textbox.send_keys(
            'Other textbox - regression testing using selenium.'
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });", footer
        )
        time.sleep(2)
        other_page.next_page_button.click()

        # Review Page
        review_page = DraftRegistrationReviewPage(driver, verify=True)

        assert review_page.title.text == 'Selenium Test Project With File Registration'
        assert (
            review_page.description.text
            == 'This is a test registration created from a project using Selenium.'
        )
        # assert review_page.category.text == 'Software'
        assert review_page.license.text == 'CC0 1.0 Universal'
        assert review_page.subject.text == 'Engineering'

        review_page.scroll_into_view(review_page.register_button.element)
        driver.execute_script(
            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });", footer
        )
        time.sleep(2)
        review_page.register_button.click()
        # On modal - click radio button to make registration public immediately
        review_page.immediate_radio_button.click()
        review_page.submit_button.click()

        # Should get redirected to am Archiving Page with Registration in Pending
        # Admin Approval status
        tombstone_page = RegistrationTombstonePage(driver, verify=True)
        assert (
            tombstone_page.tombstone_title.text
            == 'Selenium Test Project With File Registration'
        )

    @pytest.mark.skip(reason='Schema are different on different environments')
    def test_submit_no_project_registration(
        self, driver, registration_user_session, add_new_page
    ):
        """This test creates a new 'no project' draft registration starting from the
        Add New Registration page.  The test uses the Open-Ended schema template and
        enters data in all of the required template fields while leaving most of the
        other data fields empty. The completed draft registration is submitted and
        made public immediately (not embargoed). A project is automatically created
        as a result of submitting the registration. This associated project is then
        deleted as cleanup. The registration is permanent and cannot be deleted.
        """

        # Verify that the Project listbox is not displayed since the No radio button is
        # selected by default
        assert add_new_page.project_listbox_trigger.absent()

        # Select 'Open-Ended Registration' from the Schema listbox
        add_new_page.schema_listbox_trigger.click()
        time.sleep(2)
        add_new_page.select_from_dropdown_listbox('Open-Ended Registration')

        # Click the Create draft button and verify that we go to the Draft Registration
        # Metadata page
        time.sleep(1)
        driver.execute_script(
            'arguments[0].scrollIntoView(true);',
            driver.find_element(By.XPATH, "//button[.//span[text()='Create draft']]"),
        )
        time.sleep(1)
        add_new_page.create_draft_button.click()
        metadata_page = DraftRegistrationMetadataPage(driver, verify=True)

        # Enter data in the input fields on the Draft Metadata page
        metadata_page.title_input.clear()
        metadata_page.title_input.send_keys('Selenium Test No Project Registration')

        metadata_page.description_textarea.click()
        metadata_page.description_textarea.send_keys(
            'This is a test registration created using Selenium.'
        )

        metadata_page.scroll_into_view(metadata_page.license_listbox_trigger.element)
        metadata_page.license_listbox_trigger.click()
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    '[role="option"]',
                )
            )
        )
        metadata_page.select_from_dropdown_listbox('CC0 1.0 Universal')

        metadata_page.scroll_into_view(metadata_page.tags_input_box.element)
        metadata_page.select_top_level_subject('Engineering')
        time.sleep(1)
        WebDriverWait(driver, 5).until(
            EC.visibility_of(metadata_page.first_selected_subject)
        )
        assert metadata_page.first_selected_subject.text == 'Engineering'

        metadata_page.tags_input_box.click()
        metadata_page.tags_input_box.send_keys('selenium\r')

        # Click Next button to go to Draft Summary Page
        metadata_page.scroll_into_view(metadata_page.next_page_button.element)
        time.sleep(1)
        footer = driver.find_element(By.CSS_SELECTOR, 'osf-footer')
        driver.execute_script(
            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });", footer
        )
        time.sleep(1)
        metadata_page.next_page_button.click()

        summary_page = DraftRegistrationSummaryPage(driver, verify=True)
        assert summary_page.page_heading.text == 'Summary'

        # Enter data into Summary field
        summary_input_field = driver.find_element(
            By.XPATH,
            "//textarea[contains(@class, 'p-textarea') and contains(@class, 'w-full')]",
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });",
            summary_input_field,
        )
        time.sleep(1)
        summary_input_field.send_keys('Test summary AQA')
        # Click Review button to go to Draft Review Page
        summary_page.scroll_into_view(summary_page.next_page_button.element)
        time.sleep(1)
        footer = driver.find_element(By.CSS_SELECTOR, 'osf-footer')
        driver.execute_script(
            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });", footer
        )
        time.sleep(1)
        summary_page.next_page_button.click()

        review_page = DraftRegistrationReviewPage(driver, verify=True)
        review_page.loading_indicator.here_then_gone()

        assert review_page.title.text == 'Selenium Test No Project Registration'
        assert (
            review_page.description.text
            == 'This is a test registration created using Selenium.'
        )
        # assert review_page.category.text == 'Software'
        assert review_page.license.text == 'CC0 1.0 Universal'
        assert review_page.subject.text == 'Engineering'
        assert review_page.tags.text == 'selenium'

        time.sleep(1)
        footer = driver.find_element(By.CSS_SELECTOR, 'osf-footer')
        driver.execute_script(
            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });", footer
        )
        time.sleep(1)

        review_page.register_button.click()

        # On modal - click radio button to make registration public immediately
        review_page.immediate_radio_button.click()
        review_page.submit_button.click()

        # Since this registration does not have any files the archiving process should
        # be very fast in the testing environments and the archiving tombstone page will
        # be visible for a second or two at most. Then we will be redirected to the
        # Registrations Detail page.

        time.sleep(5)
        current_url = driver.current_url

        project_guid = current_url.split('osf.io/', 1)[1]
        print(project_guid)

        osf_api.delete_project(registration_user_session, project_guid, None)

        # NOTE: As with the Submit Registration with Project test above we will allow
        # the automatic approval process to approve each registration which in the
        # testing environments typically occurs within a few hours.


@markers.dont_run_on_prod
@pytest.mark.usefixtures('must_be_logged_in_as_registration_user')
@markers.core_functionality
class TestRegistrationFilesPages:
    @pytest.fixture()
    def registration_guid(self, session):
        registration_guid = osf_api.get_registration_by_title(
            'Selenium Registration to Test Files Page'
        )
        return registration_guid

    @pytest.fixture()
    def registration_files_page(self, driver, registration_guid):
        registration_files_page = RegistrationFilesListPage(
            driver, guid=registration_guid
        )
        registration_files_page.goto()
        return registration_files_page

    @pytest.fixture
    def files_list_page(self, driver, login_as_user_with_registrations):
        """Return the Files List page for a registration with a file"""

        # First start at the My Registrations page
        my_registrations_page = MyRegistrationsPage(driver)
        time.sleep(1)
        my_registrations_page.goto()
        time.sleep(2)

        # Wait for registration cards to load on page
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.p-card-body'))
        )
        registration_cards = my_registrations_page.registration_cards
        assert registration_cards

        # # Find the first registration card for a registration that has a file

        title = 'Selenium Test Project With File Registration'

        view_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    f"//h2[normalize-space(text())='{title}']//following::button[.//span[normalize-space()='View']][1]",
                )
            )
        )

        view_button.click()

        # Get the registration's node id from URL.
        # Get the registration's node id from the card's title link and then use the
        # node id to navigate to the File List page for the registration.
        time.sleep(3)
        current_url = driver.current_url

        node_id = current_url.split('osf.io/', 1)[1]
        print(node_id)
        files_list_page = RegistrationFilesListPage(driver, guid=node_id)
        # files_list_page.goto()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'registration-files'))
        ).click()
        time.sleep(3)
        assert RegistrationFilesListPage(driver, verify=True)

        # Click the 'Archive of OSF Storage' button to expand the list of files
        files_list_page.file_list_button.click()

        # Wait for file list items to load on page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.entry-title'))
        )
        return files_list_page

    def wait_until_page_ready(self, driver, timeout=30):
        wait = WebDriverWait(driver, timeout)

        wait.until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'p-progress-spinner'))
        )

    def verify_embed_links(self, page):
        """Helper function to verify the copy to clipboard functionality of the Embed
        links on the Registration File pages.
        """

        # Click Embed link and then click the Copy dynamic JS iFrane link from the
        # secondary menu
        page.embed_link.click()
        page.copy_js_link.click()
        # Verify data copied to clipboard
        window = tkinter.Tk()
        window.withdraw()  # to hide the window
        clipboard_value = window.clipboard_get()
        assert page.copy_js_link.get_attribute('data-clipboard-text') == clipboard_value

        # Next click the Copy static HTML iFrane link from secondary menu
        page.copy_html_link.click()
        # Verify data copied to clipboard
        clipboard_value = window.clipboard_get()
        assert (
            page.copy_html_link.get_attribute('data-clipboard-text') == clipboard_value
        )

    def verify_download_link(self, driver, page, file_name, wait_selector):
        """Helper function to verify the file download functionality on the Registration
        File pages.
        """

        # If running on local machine, first check if the file already exists in the
        # Downloads folder. If so then delete the old copy before attempting to download
        # a new one.
        if settings.DRIVER != 'Remote':
            file_path = os.path.expanduser('~/Downloads/' + file_name)
            if os.path.exists(file_path):
                os.remove(file_path)

        # Verify that the file is actually downloaded to user's machine
        current_date = datetime.datetime.now()
        if settings.DRIVER == 'Remote':
            # First verify the downloaded file exists on the virtual remote machine
            assert driver.execute_script(
                'browserstack_executor: {"action": "fileExists", "arguments": {"fileName": "%s"}}'
                % (file_name)
            )
            # Next get the file properties and then verify that the file creation date
            # is today
            file_props = driver.execute_script(
                'browserstack_executor: {"action": "getFileProperties", "arguments": {"fileName": "%s"}}'
                % (file_name)
            )
            file_create_date = datetime.datetime.fromtimestamp(
                file_props['created_time']
            )
            assert file_create_date.date() == current_date.date()
        else:
            # First verify the downloaded file exists
            assert os.path.exists(file_path)
            # Next verify the file was downloaded today
            file_mtime = os.path.getmtime(file_path)
            file_mod_date = datetime.datetime.fromtimestamp(file_mtime)
            assert file_mod_date.date() == current_date.date()

    def test_files_list_page(self, driver, registration_files_page):
        """Test the functionality available on the Files List page of a registration
        with a file.
        """

        # Click the File Options button for the search file listed
        file_name = 'aaa_selenium.txt'
        assert RegistrationFilesListPage(driver, verify=True)
        registration_files_page.archive_link.click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.entry-title'))
        )
        # Search for file
        row = find_file_by_search(registration_files_page, target_file_name=file_name)
        assert row is not None

    @pytest.mark.skip(reason='ENG-9640')
    def test_file_detail_page(self, driver, registration_files_page):
        """Test the functionality available on the Registration File Detail page"""

        # Click the first file on the Files List page to open the File Detail page in a
        # new tab
        # Click the File Options button for the search file listed
        file_name = 'aaa_selenium.txt'
        assert RegistrationFilesListPage(driver, verify=True)
        registration_files_page.archive_link.click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.entry-title'))
        )
        # Search for file
        registration_files_page.click_on_file_link(file_name)
        try:
            # Wait for the new tab to open - window count should then = 2
            WebDriverWait(driver, 5).until(EC.number_of_windows_to_be(2))

            # Switch focus to the new tab
            driver.switch_to.window(driver.window_handles[1])
            file_detail_page = RegistrationFileDetailPage(driver, verify=True)

            # Wait for File Renderer to load
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'iframe'))
            )

            # Click the File Options button
            file_detail_page.first_file_options_button.click()

            # if settings.DRIVER != 'Remote':  # Can't access clipboard on remote machine
            #     self.verify_embed_links(file_detail_page)

            file_name = file_detail_page.file_name.text

            # Verify file download
            self.verify_download_link(driver, file_detail_page, file_name, 'iframe')

            # Click the button to reveal the Revisions section of the page
            file_detail_page.versions_button.click()

            # Next click the toggle button for the first revision line item to reveal
            # more options
            file_detail_page.first_revision_toggle_button.click()

            if settings.DRIVER != 'Remote':  # Can't access clipboard on remote machine
                # Click the Copy MD5 link
                file_detail_page.copy_md5_link.click()
                # Verify data copied to clipboard
                window = tkinter.Tk()
                window.withdraw()  # to hide the window
                clipboard_value = window.clipboard_get()
                assert (
                    file_detail_page.copy_md5_link.get_attribute('data-clipboard-text')
                    == clipboard_value
                )

                # Next click the Copy SHA-2 link
                file_detail_page.copy_sha2_link.click()
                # Verify data copied to clipboard
                clipboard_value = window.clipboard_get()
                assert (
                    file_detail_page.copy_sha2_link.get_attribute('data-clipboard-text')
                    == clipboard_value
                )

            # Click the button to reveal the Tags section of the page
            file_detail_page.tags_button.click()

            # Add a timestamp as a new tag
            timestamp = str(datetime.datetime.now())
            file_detail_page.tags_input_box.click()
            file_detail_page.tags_input_box.send_keys(timestamp)
            file_detail_page.tags_input_box.send_keys(Keys.ENTER)

            # Verify timestamp tag was added
            assert file_detail_page.get_tag(timestamp) is not None

        finally:
            # Close the second tab that was opened. We do not want subsequent tests to
            # use the second tab.
            driver.close()
            # Switch focus back to the first tab
            driver.switch_to.window(driver.window_handles[0])

    def test_file_download(self, driver, registration_files_page):
        """Test file download functionality available on the Registration Files page"""
        # Click the File Options button for the search file listed
        file_name = 'download_file_for_registration.txt'
        assert RegistrationFilesListPage(driver, verify=True)
        registration_files_page.archive_link.click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.entry-title'))
        )
        # Search for file and click on menu button for the file
        find_file_by_search(registration_files_page, target_file_name=file_name)
        registration_files_page.click_on_menu_button()
        # Click on download button
        registration_files_page.click_on_download_button()
        registration_files_page.reload()
        self.wait_until_page_ready(driver)
        # Verify that downloaded file is available in the path
        self.verify_download_link(driver, registration_files_page, file_name, 'i-frame')

    def test_download_as_zip(self, driver, registration_files_page):
        """Test file download functionality available on the Registration Files page"""
        # Click the File Options button for the search file listed

        assert RegistrationFilesListPage(driver, verify=True)
        # Get the archive name
        archive_name = registration_files_page.archive_link.text.strip() + '.zip'
        registration_files_page.archive_link.click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.entry-title'))
        )
        # Click on the Download as Zip button in Files page
        registration_files_page.click_on_button('Download As Zip')
        registration_files_page.reload()
        self.wait_until_page_ready(driver)
        # Verify that downloaded file is available in the path
        self.verify_download_link(
            driver, registration_files_page, archive_name, 'i-frame'
        )

    def test_sort_name_a_to_z(self, driver, registration_files_page):
        """Test to verify sorting by name from A to Z for given addon in
        registration files page.
        """
        # Navigate to files page
        assert RegistrationFilesListPage(driver, verify=True)
        registration_files_page.archive_link.click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.entry-title'))
        )

        # Wait for File List items to load
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located(
                (By.XPATH, '//circle[@class=“p-progressspinner-circle”]')
            )
        )

        registration_files_page.select_sort_from_list('Name: A-Z')
        sorted_rows = driver.find_elements_by_xpath('//span[@class="entry-title"]')
        ui_list = [row.text.strip() for row in sorted_rows]
        expected_sorted_list = sorted(ui_list, key=str.lower)
        assert ui_list == expected_sorted_list

    def test_sort_name_z_to_a(self, driver, registration_files_page):
        """Test to verify sorting by name from Z to A for given addon in
        project files page.
        """
        # Navigate to files page
        assert RegistrationFilesListPage(driver, verify=True)
        registration_files_page.archive_link.click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.entry-title'))
        )

        # Wait for File List items to load
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located(
                (By.XPATH, '//circle[@class=“p-progressspinner-circle”]')
            )
        )

        registration_files_page.select_sort_from_list('Name: Z-A')
        sorted_rows = driver.find_elements_by_xpath('//span[@class="entry-title"]')
        ui_list = [row.text.strip() for row in sorted_rows]
        expected_sorted_list = sorted(ui_list, key=str.lower)
        assert ui_list == expected_sorted_list

    def test_sort_modified_date_descending(self, driver, registration_files_page):
        """Test to verify sorting by name from A to Z for given addon in
        project files page.
        """
        # Navigate to files page
        assert RegistrationFilesListPage(driver, verify=True)
        registration_files_page.archive_link.click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.entry-title'))
        )

        # Wait for File List items to load
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located(
                (By.XPATH, '//circle[@class=“p-progressspinner-circle”]')
            )
        )

        registration_files_page.select_sort_from_list('Last modified: oldest to newest')
        self.wait_until_page_ready(driver)
        sorted_rows = driver.find_elements_by_xpath(
            '//div[@class="files-table-cell"][3]'
        )
        date_list = [row.text.strip() for row in sorted_rows]
        ui_dates = [
            datetime.datetime.strptime(item, '%b %d, %Y %I:%M %p') for item in date_list
        ]
        assert ui_dates == sorted(ui_dates)

    def test_sort_modified_date_ascending(self, driver, registration_files_page):
        """Test to verify sorting by name from A to Z for given registration files page."""

        # Navigate to files page
        assert RegistrationFilesListPage(driver, verify=True)
        registration_files_page.archive_link.click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.entry-title'))
        )

        # Wait for File List items to load
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located(
                (By.XPATH, '//circle[@class=“p-progressspinner-circle”]')
            )
        )

        registration_files_page.select_sort_from_list('Last modified: newest to oldest')
        sorted_rows = driver.find_elements_by_xpath(
            '//div[@class="files-table-cell"][3]'
        )

        date_list = [row.text.strip() for row in sorted_rows]
        ui_dates = [
            datetime.datetime.strptime(item, '%b %d, %Y %I:%M %p') for item in date_list
        ]
        assert ui_dates == sorted(ui_dates, reverse=True)
