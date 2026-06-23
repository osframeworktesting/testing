import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import markers
from pages.base import BasePage
from pages.file_detail import FileDetailPage
from pages.preprints import PreprintDetailPage
from pages.project import ProjectPage
from pages.registries import RegistrationDetailPage
from pages.search import (
    FileSearchResults,
    PreprintSearchResults,
    ProjectSearchResults,
    RegistrationSearchResults,
    SearchPage,
    SearchPageHelpers,
    UserSearchResults,
)
from pages.user import UserProfilePage
from utils import wait_until_page_ready


@pytest.fixture()
def search_page(driver):
    search_page = SearchPage(driver)
    search_page.goto_short()
    return search_page


@pytest.fixture()
def search_page_short(driver):
    search_page = SearchPageHelpers(driver)
    search_page.goto_short()
    return search_page


@pytest.fixture()
def registration_search_page(driver):
    reg_search_page = RegistrationSearchResults(driver)
    reg_search_page.goto()
    return reg_search_page


@pytest.fixture()
def preprint_search_page(driver):
    preprint_search_page = PreprintSearchResults(driver)
    preprint_search_page.goto()
    return preprint_search_page


@pytest.fixture()
def project_search_page(driver):
    project_search_page = ProjectSearchResults(driver)
    project_search_page.goto()
    return project_search_page


@pytest.fixture()
def user_search_page(driver):
    user_search_page = UserSearchResults(driver)
    user_search_page.goto()
    return user_search_page


@pytest.fixture()
def file_search_page(driver):
    file_search_page = FileSearchResults(driver)
    file_search_page.goto()
    return file_search_page


def normalize_ui_date(date_string):
    try:
        # The date from the search card is formatted (February 17, 2026)
        return datetime.strptime(date_string, '%B %d, %Y').date()
    except ValueError:
        # Registration overview page date is formatted (Feb 17, 2026, 10:51 AM)
        dt = datetime.strptime(date_string, '%b %d, %Y, %I:%M %p')
        dt = dt.replace(tzinfo=ZoneInfo('America/New_York'))
        return dt.astimezone(ZoneInfo('UTC')).date()


@markers.smoke_test
@markers.core_functionality
@pytest.mark.usefixtures('throttle_on_prod')
class SearchPageBase:
    def wait_until_page_ready(self, driver, timeout=15):
        wait = WebDriverWait(driver, timeout)

        wait.until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

        try:
            wait.until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, 'p-progress-spinner')
                )
            )
        except TimeoutException:
            pass


@markers.smoke_test
@markers.core_functionality
@pytest.mark.usefixtures('throttle_on_prod')
class TestSearchPage(SearchPageBase):
    def test_search_results_exist_all_tab(self, driver, search_page):
        search_page.search_input.send_keys('test')
        search_page.search_input.send_keys(Keys.ENTER)
        search_page.loading_indicator.here_then_gone()
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
            )
        )
        assert len(search_page.search_results) > 0

    def test_search_results_exist_projects_tab(self, driver, search_page):
        search_page.search_input.send_keys('test')
        search_page.search_input.send_keys(Keys.ENTER)
        search_page.loading_indicator.here_then_gone()
        # Switch to the Projects Tab
        search_page.projects_tab_link.click()
        search_page.loading_indicator.here_then_gone()
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
            )
        )
        assert len(search_page.search_results) > 0
        # Verify that first search result is of Project type
        assert search_page.first_card_object_type_label.text[:7] == 'Project'

    def test_search_results_exist_registrations_tab(self, driver, search_page):
        search_page.search_input.send_keys('test')
        search_page.search_input.send_keys(Keys.ENTER)
        search_page.loading_indicator.here_then_gone()
        # Switch to the Registrations Tab
        search_page.registrations_tab_link.click()
        search_page.loading_indicator.here_then_gone()
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
            )
        )
        assert len(search_page.search_results) > 0
        # Verify that first search result is of Registration type
        assert search_page.first_card_object_type_label.text[:12] == 'Registration'

    def test_search_results_exist_preprints_tab(self, driver, search_page):
        search_page.search_input.send_keys('test')
        search_page.search_input.send_keys(Keys.ENTER)
        search_page.loading_indicator.here_then_gone()
        # Switch to the Preprints Tab
        search_page.preprints_tab_link.click()
        search_page.loading_indicator.here_then_gone()
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
            )
        )
        assert len(search_page.search_results) > 0
        # Verify that first search result is of Preprint type
        assert search_page.first_card_object_type_label.text == 'Preprint'

    def test_search_results_exist_files_tab(self, driver, search_page):
        search_page.search_input.send_keys('test')
        search_page.search_input.send_keys(Keys.ENTER)
        search_page.loading_indicator.here_then_gone()
        # Switch to the Files Tab
        search_page.files_tab_link.click()
        search_page.loading_indicator.here_then_gone()
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
            )
        )
        assert len(search_page.search_results) > 0
        # Verify that first search result is of File type
        assert search_page.first_card_object_type_label.text == 'File'


class TestSearchPageAllTab(SearchPageBase):
    @pytest.mark.skip(reason='ENG-10674')
    def test_filtering_by_creator_on_all_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        search_page_short.check_filtering_by_creator(driver)

    def test_filtering_by_date_created_on_all_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        search_page_short.check_filtering_by_date_created(driver, 'Date created')

    @pytest.mark.skip(reason='ENG-10674')
    def test_filtering_by_funder_on_all_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_funder(driver)

    def test_filtering_by_subject_on_all_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        search_page_short.check_filtering_by_subject(driver)

    def test_filtering_by_license_on_all_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        search_page_short.check_filtering_by_license(driver)

    def test_filtering_by_resource_type_on_all_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        base_page = BasePage(driver)
        wait = WebDriverWait(driver, 15)

        # 1. Expand Resource Type menu
        resource_type_menu = wait.until(
            EC.presence_of_element_located(search_page_short.resource_type_menu_locator)
        )
        base_page.scroll_to(resource_type_menu)

        resource_type_menu.click()

        # Click 'Select Resource Type' drop-down menu
        resource_type_multiselect_dropdown = wait.until(
            EC.visibility_of_element_located(
                search_page_short.resource_type_multiselect_dropdown_selector
            )
        )
        resource_type_multiselect_dropdown.click()
        wait_until_page_ready(driver)

        input_filed_locator = (
            By.XPATH,
            "//input[@role='searchbox' and contains(@class,'p-multiselect-filter')]",
        )
        wait.until(EC.visibility_of_element_located(input_filed_locator)).send_keys(
            'preprin'
        )
        wait_until_page_ready(driver)
        # Save name of the selected option (Resource Type)
        name_of_record = search_page_short.get_record_name(driver, '1')

        # Save number of records related to the selected Resource Type
        number_of_records = search_page_short.get_record_count(driver, '1')

        # Select First option from the list
        wait_until_page_ready(driver)
        resource_type_first_option_locator = (
            By.XPATH,
            '(//ul[@role="listbox"]//li[@role="option"]//input[@type="checkbox"])[1]',
        )

        wait.until(
            EC.presence_of_element_located(resource_type_first_option_locator)
        ).click()

        wait_until_page_ready(driver)

        # CHeck if results displays correct number of results.
        result_count_after_filter_applying = search_page_short.get_results_count(driver)
        assert result_count_after_filter_applying <= number_of_records

        # Check if cards in filtering results contains correct 'Resource Type'.

        resource_type_in_card_locator = (
            By.XPATH,
            f"//p[contains(@class,'type') and normalize-space()='{name_of_record}']",
        )

        assert wait.until(
            EC.presence_of_element_located(resource_type_in_card_locator)
        ).is_displayed()

    @pytest.mark.skip(reason='ENG-10674')
    def test_filtering_by_part_of_collection_on_all_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        base_page = BasePage(driver)
        wait = WebDriverWait(driver, 15)

        # 1. Expand "Is part of collection " menu
        part_of_collection_menu = wait.until(
            EC.presence_of_element_located(
                search_page_short.part_of_collection_menu_locator
            )
        )
        base_page.scroll_to(part_of_collection_menu)

        part_of_collection_menu.click()

        # Click 'Select collection' drop-down menu
        part_of_collection_multiselect_dropdown = wait.until(
            EC.visibility_of_element_located(
                search_page_short.part_of_collection_multiselect_dropdown_selector
            )
        )
        part_of_collection_multiselect_dropdown.click()

        # Save name of the selected option (Collection)
        name_of_record = search_page_short.get_record_name(driver, '1')

        # Save number of records related to the selected Collection
        number_of_records = search_page_short.get_record_count(driver, '1')

        # Select First option from the list
        wait_until_page_ready(driver)
        collection_first_option_locator = (
            By.XPATH,
            '(//ul[@role="listbox"]//li[@role="option"]//input[@type="checkbox"])[1]',
        )

        wait.until(
            EC.presence_of_element_located(collection_first_option_locator)
        ).click()
        wait_until_page_ready(driver)

        # CHeck if results displays correct number of results.
        result_count_after_filter_applying = search_page_short.get_results_count(driver)
        assert result_count_after_filter_applying <= number_of_records

        # Expand addition menu of the firs card
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.chevron_menu_first_card_locator
            )
        ).click()

        # Check if cards in filtering results contains correct 'Collection'.
        record_locator = (By.XPATH, "(//p[contains(., ' Collection: ')]//a)[1]")

        element = wait.until(EC.presence_of_element_located(record_locator))
        base_page.scroll_to(element)

        assert name_of_record in element.text

    def test_filtering_by_provider_on_all_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        base_page = BasePage(driver)
        wait = WebDriverWait(driver, 15)

        # 1. Expand "Provider " menu
        provider_menu = wait.until(
            EC.presence_of_element_located(search_page_short.provider_menu_locator)
        )
        base_page.scroll_to(provider_menu)

        provider_menu.click()

        # Click 'Select provider' drop-down menu
        provider_multiselect_dropdown = wait.until(
            EC.visibility_of_element_located(
                search_page_short.provider_multiselect_dropdown_selector
            )
        )
        provider_multiselect_dropdown.click()

        input_filed_locator = (
            By.XPATH,
            "//input[@role='searchbox' and contains(@class,'p-multiselect-filter')]",
        )
        wait.until(EC.visibility_of_element_located(input_filed_locator)).send_keys(
            'regis'
        )
        wait_until_page_ready(driver)

        # Save name of the selected option (Provider)
        name_of_record = search_page_short.get_record_name(driver, '1')

        # Save number of records related to the selected Provider
        number_of_records = search_page_short.get_record_count(driver, '1')

        # Select First option from the list
        wait_until_page_ready(driver)
        provider_first_option_locator = (
            By.XPATH,
            '(//ul[@role="listbox"]//li[@role="option"]//input[@type="checkbox"])[1]',
        )

        wait.until(
            EC.presence_of_element_located(provider_first_option_locator)
        ).click()
        wait_until_page_ready(driver)

        # CHeck if results displays correct number of results.
        result_count_after_filter_applying = search_page_short.get_results_count(driver)
        assert result_count_after_filter_applying <= number_of_records

        # Expand addition menu of the firs card
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.chevron_menu_first_card_locator
            )
        ).click()

        # Check if cards in filtering results contains correct 'Provider'.

        record_locator = (By.XPATH, "(//p[contains(., ' Provider: ')]//a)[1]")

        element = wait.until(EC.presence_of_element_located(record_locator))
        base_page.scroll_to(element)

        assert name_of_record in element.text

    def test_filtering_by_institution_on_all_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        search_page_short.check_filtering_by_institution(driver, '3')

    def test_sorting_by_created_date_on_all_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        search_page_short.check_sorting_by_created_date(driver, 'created')

    def test_sorting_by_modified_date_on_all_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        search_page_short.check_sorting_by_modified_date(driver)

    def test_search_in_filtering_by_creator_on_all_tab(self, driver, search_page_short):
        wait = WebDriverWait(driver, 15)

        wait_until_page_ready(driver)

        # 1. Expand Creator menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.creator_dropdown_menu_selector
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.additional_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_date_created_on_all_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)

        # 1. Expand Date Created menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.date_created_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.date_created_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_funder_on_all_tab(self, driver, search_page_short):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)

        # 1. Expand Funder menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.funder_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.funder_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_subject_on_all_tab(self, driver, search_page_short):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)

        # 1. Expand Subject menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.subject_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.subject_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_license_on_all_tab(self, driver, search_page_short):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)

        # 1. Expand License menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.license_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.license_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_resource_type_on_all_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)

        # 1. Expand Resource Type menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.resource_type_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.resource_type_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_institution_on_all_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)

        # 1. Expand Institution menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.institution_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.institution_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_provider_on_all_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)

        # 1. Expand Provider menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.provider_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.provider_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver, '2')

    def test_search_in_filtering_by_part_of_collection_on_all_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)

        # 1. Expand Part of Collection menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.part_of_collection_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.part_of_collection_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_card_all(self, driver, search_page):
        WebDriverWait(driver, 25).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
        )
        assert len(search_page.search_results) > 0

        # Use the osfstoppropagation locator to determine the type of the first search result
        result_type = search_page.node_type.text.strip()

        dispatch = {
            'Project': lambda: TestSearchPageProjectsTab().test_search_card_projects(
                driver, ProjectSearchResults(driver)
            ),
            'Registration': lambda: TestSearchPageRegistrationsTab().test_search_card_registrations(
                driver, RegistrationSearchResults(driver)
            ),
            'Preprint': lambda: TestSearchPagePreprintsTab().test_search_card_preprints(
                driver, PreprintSearchResults(driver)
            ),
            'File': lambda: TestSearchPageFilesTab().test_search_card_files(
                driver, FileSearchResults(driver)
            ),
            'User': lambda: TestSearchPageUsersTab().test_search_card_users(
                driver, UserSearchResults(driver)
            ),
        }

        # Refresh search results up to 3 times in case we hit a component, withdrawn registration, or other type
        for attempt in range(3):
            if result_type in dispatch:
                break
            if attempt < 2:
                driver.refresh()
                WebDriverWait(driver, 25).until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, 'osf-resource-card')
                    )
                )
                result_type = search_page.node_type.text.strip()
        else:
            pytest.fail(f'Unknown search result type: {result_type!r}')

        dispatch[result_type]()


class TestSearchPagePreprintsTab(SearchPageBase):
    def test_filtering_by_creator_on_preprints_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_creator(driver)

    def test_filtering_by_date_created_on_preprints_tab(
        self, driver, search_page_short
    ):
        # Open preprints tab
        wait_until_page_ready(driver)
        # wait.until(EC.element_to_be_clickable(search_page_short.preprints_tab_link_xpath)).click()
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_date_created(driver, 'Date created')

    def test_filtering_by_subject_on_preprints_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_subject(driver)

    def test_filtering_by_license_on_preprints_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_license(driver)

    @pytest.mark.skip(reason='ENG-10674')
    def test_filtering_by_institution_on_preprints_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_institution(driver)

    def test_filtering_by_provider_on_preprints_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_provider(driver)

    def test_filtering_by_supplemental_materials_on_preprints_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_supplemental_materials(driver)

    def test_filtering_by_data_on_preprints_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)
        public_data_xpath = "//section[.//h3[normalize-space()='Public Data']]//p[contains(text(),'http')]"
        search_page_short.check_filtering_by_data(driver, public_data_xpath)

    def test_filtering_by_preregistered_analysis_plan_on_preprints_tab(
        self, driver, search_page_short
    ):
        base_page = BasePage(driver)
        wait = WebDriverWait(driver, 25)
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Additional Filters menu
        additional_filters_menu = wait.until(
            EC.visibility_of_element_located(
                search_page_short.additional_filters_menu_locator
            )
        )
        additional_filters_menu.click()

        # Select 'preregistered_analysis_plan' option
        preregistered_analysis_plan_option_locator = (
            By.XPATH,
            "//input[@id='checkbox-hasPreregisteredAnalysisPlan']",
        )
        preregistered_analysis_plan_option = wait.until(
            EC.presence_of_element_located(preregistered_analysis_plan_option_locator)
        )
        base_page.scroll_to(preregistered_analysis_plan_option)

        # Save number of records related to the selected option 'preregistered_analysis_plan'
        number_of_records = search_page_short.get_record_count_for_additional_filters(
            driver, 'Preregistered analysis plan'
        )

        # Select 'preregistered_analysis_plan' option from the list
        wait.until(
            EC.presence_of_element_located(preregistered_analysis_plan_option_locator)
        ).click()
        wait_until_page_ready(driver)

        # CHeck if results displays correct number of results.
        result_count_after_filter_applying = search_page_short.get_results_count(driver)
        assert result_count_after_filter_applying <= number_of_records

        # Expand addition menu of the firs card
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.chevron_menu_first_card_locator
            )
        ).click()
        wait_until_page_ready(driver)

        #
        element_on_card = (
            By.XPATH,
            "//p[contains(.,'Associated preregistration')]//a[contains(@href,'http')]",
        )

        assert wait.until(
            EC.visibility_of_element_located(element_on_card)
        ).is_displayed()

    def test_filtering_by_preregistered_study_design_on_preprints_tab(
        self, driver, search_page_short
    ):
        base_page = BasePage(driver)
        wait = WebDriverWait(driver, 25)
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Additional Filters menu
        additional_filters_menu = wait.until(
            EC.visibility_of_element_located(
                search_page_short.additional_filters_menu_locator
            )
        )
        additional_filters_menu.click()

        # Select 'preregistered_study_design' option
        preregistered_study_design_option_locator = (
            By.XPATH,
            "//input[@id='checkbox-hasPreregisteredStudyDesign']",
        )
        preregistered_study_design_option = wait.until(
            EC.presence_of_element_located(preregistered_study_design_option_locator)
        )
        base_page.scroll_to(preregistered_study_design_option)

        # Save number of records related to the selected option 'preregistered_study_design'
        number_of_records = search_page_short.get_record_count_for_additional_filters(
            driver, 'Preregistered study design'
        )

        # Select 'preregistered_study_design' option from the list
        wait.until(
            EC.presence_of_element_located(preregistered_study_design_option_locator)
        ).click()
        wait_until_page_ready(driver)

        # CHeck if results displays correct number of results.
        result_count_after_filter_applying = search_page_short.get_results_count(driver)
        assert result_count_after_filter_applying <= number_of_records

        # Expand addition menu of the firs card
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.chevron_menu_first_card_locator
            )
        ).click()
        wait_until_page_ready(driver)

        #
        element_on_card = (
            By.XPATH,
            "//p[contains(.,'Associated study design')]//a[contains(@href,'http')]",
        )

        assert wait.until(
            EC.visibility_of_element_located(element_on_card)
        ).is_displayed()

    def test_clearing_of_applied_filters_on_preprints_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_clearing_of_applied_filters(driver)

    def test_search_card_preprints(self, driver, preprint_search_page):
        WebDriverWait(driver, 25).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
        )

        assert len(preprint_search_page.search_results) > 0

        # Collect information from first search result
        preprint_title = preprint_search_page.preprint_title.text
        search_date_text_full = preprint_search_page.date_created.text
        search_card_date = search_date_text_full.split('Date created:')[1].strip()

        # Collect contributors from search card before navigating
        card_contributor_elements = preprint_search_page.preprint_card_contributor_links
        card_contributor_names = [
            el.text.strip().rstrip(',').strip() for el in card_contributor_elements
        ]
        has_more_contributors = (
            preprint_search_page.preprint_card_contributors_more.present()
        )
        more_count = 0
        if has_more_contributors:
            more_text = preprint_search_page.preprint_card_contributors_more.text
            match = re.search(r'\d+', more_text)
            more_count = int(match.group()) if match else 0

        preprint_search_page.preprint_title.click_expecting_popup()
        WebDriverWait(driver, 25).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-preprint-details'))
        )
        wait_until_page_ready(driver)

        # Collect information from preprint overview page
        preprint_detail = PreprintDetailPage(driver)
        preprint_detail_title = preprint_detail.preprint_title.element.text

        # The submitted date bar is not present on all preprint providers/states,
        has_date_on_detail = preprint_detail.date_created.present()
        if has_date_on_detail:
            preprint_date_text_full = preprint_detail.date_created.text
            preprint_date_created = preprint_date_text_full.split('Submitted:')[
                1
            ].strip()

        # Wait for contributors list to finish rendering before reading
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[data-test-contributor-name]')
                )
            )
        except TimeoutException:
            pass  # Genuinely no contributors on this preprint

        detail_contributor_names = [
            el.text.strip().rstrip(',').strip()
            for el in preprint_detail.all_contributors
        ]
        assert preprint_title == preprint_detail_title
        if has_date_on_detail:
            assert normalize_ui_date(search_card_date) == normalize_ui_date(
                preprint_date_created
            )

        try:
            total_on_detail = len(detail_contributor_names)
            if total_on_detail == 0:
                # No contributors
                assert len(card_contributor_names) == 0
                assert not has_more_contributors
            elif total_on_detail <= 4:
                # Use sorted() because display order may differ between card and detail.
                assert sorted(card_contributor_names) == sorted(
                    detail_contributor_names
                )
                assert not has_more_contributors
            else:
                # 5+ contributors: a subset shown by name, rest as "and X more".
                # Use sets for the membership check (handles duplicate display names).
                card_name_set = set(card_contributor_names)
                detail_name_set = set(detail_contributor_names)
                assert card_name_set.issubset(
                    detail_name_set
                ), f'Card contributors {card_name_set} are not all present on detail page {detail_name_set}'
                assert has_more_contributors
                assert more_count == total_on_detail - len(card_contributor_names)
        except AssertionError:
            print(f'\nPreprint URL: {driver.current_url}')
            raise

    def test_sorting_by_created_date_on_preprints_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_sorting_by_created_date(driver, 'created')

    def test_sorting_by_modified_date_on_preprints_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_sorting_by_modified_date(driver)

    def test_search_in_filtering_by_creator_on_preprints_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Creator menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.creator_dropdown_menu_selector
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.additional_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_date_created_on_preprints_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Date Created menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.date_created_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.date_created_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_subject_on_preprints_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Subject menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.subject_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.subject_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_license_on_preprints_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand License menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.license_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.license_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_institution_on_preprints_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Institution menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.institution_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.institution_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_provider_on_preprints_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open preprints tab
        search_page_short.preprints_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Provider menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.provider_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.provider_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)


class TestSearchPageRegistrationsTab(SearchPageBase):
    def test_filtering_by_creator_on_registrations_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_creator(driver)

    def test_filtering_by_date_created_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_date_created(driver, 'Date registered')

    def test_filtering_by_subject_on_registrations_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_subject(driver)

    def test_filtering_by_license_on_registrations_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_license(driver)

    def test_filtering_by_institution_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_institution(driver)

    def test_filtering_by_provider_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_provider(driver)

    @pytest.mark.skip(reason='ENG-10674')
    def test_filtering_by_funder_on_registrations_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_funder(driver)

    def test_filtering_by_resource_type_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_resource_type(driver, '', 'Registration')

    def test_filtering_by_data_registrations_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)
        data_xpath = "//i[contains(@class,'custom-icon-data')]"

        search_page_short.check_filtering_by_data(driver, data_xpath)

    def test_filtering_by_registration_template_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 25)
        base_page = BasePage(driver)

        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand "registration_template" menu
        registration_template_menu = wait.until(
            EC.presence_of_element_located(
                search_page_short.registration_template_menu_locator
            )
        )
        base_page.scroll_to(registration_template_menu)

        registration_template_menu.click()

        # Click 'Select registration_template' drop-down menu
        registration_template_multiselect_dropdown = wait.until(
            EC.visibility_of_element_located(
                search_page_short.registration_template_multiselect_dropdown_selector
            )
        )
        registration_template_multiselect_dropdown.click()

        # Save name of the selected option (Template)
        name_of_record = search_page_short.get_record_name(driver, '1')

        # Save number of records related to the selected Template
        number_of_records = search_page_short.get_record_count(driver, '1')

        # Select First option from the list
        wait_until_page_ready(driver)
        template_first_option_locator = (
            By.XPATH,
            '(//ul[@role="listbox"]//li[@role="option"]//input[@type="checkbox"])[1]',
        )

        wait.until(
            EC.presence_of_element_located(template_first_option_locator)
        ).click()
        wait_until_page_ready(driver)

        # CHeck if results displays correct number of results.
        result_count_after_filter_applying = search_page_short.get_results_count(driver)
        assert result_count_after_filter_applying <= number_of_records

        # Expand addition menu of the firs card
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.chevron_menu_first_card_locator
            )
        ).click()

        # Check if cards in filtering results contains correct 'Template'.
        record_locator = (
            By.XPATH,
            "//p[contains(normalize-space(),'Registration Template')]",
        )

        element = wait.until(EC.presence_of_element_located(record_locator))
        base_page.scroll_to(element)

        assert name_of_record in element.text

    def test_filtering_by_includes_community_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_includes_community_schema(driver)

    def test_filtering_by_analytic_code_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        selected_option_checkbox = 'hasAnalyticCodeResource'
        additional_option_name = 'Analytic code'
        icon_xpath = "//i[contains(@class,'custom-icon-code')]"

        search_page_short.check_filtering_by_additional_options(
            driver, selected_option_checkbox, additional_option_name, icon_xpath
        )

    def test_filtering_by_papers_on_registrations_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        selected_option_checkbox = 'hasPapersResource'
        additional_option_name = 'Papers'
        icon_xpath = "//i[contains(@class,'custom-icon-papers')]"

        search_page_short.check_filtering_by_additional_options(
            driver, selected_option_checkbox, additional_option_name, icon_xpath
        )

    def test_filtering_by_supplemental_resource_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        selected_option_checkbox = 'hasSupplementalResource'
        additional_option_name = 'Supplemental resource'
        icon_xpath = "//i[contains(@class,'custom-icon-supplements')]"

        search_page_short.check_filtering_by_additional_options(
            driver, selected_option_checkbox, additional_option_name, icon_xpath
        )

    def test_filtering_by_materials_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()

        selected_option_checkbox = 'hasMaterialsResource'
        additional_option_name = 'Materials'
        icon_xpath = "//i[contains(@class,'custom-icon-supplements')]"

        search_page_short.check_filtering_by_additional_options(
            driver, selected_option_checkbox, additional_option_name, icon_xpath
        )

    def test_clearing_of_applied_filters_on_registration_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_clearing_of_applied_filters(driver)

    def test_search_card_registrations(self, driver, registration_search_page):
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
        )

        assert len(registration_search_page.search_results) > 0

        withdrawn_badge = driver.find_elements(
            By.XPATH,
            '(//osf-resource-card)[1]//p-tag[contains(normalize-space(.), "Withdrawn")]',
        )
        if withdrawn_badge:
            pytest.skip('Withdrawn Registration')

        # Collect contributors from search card before navigating
        card_contributor_elements = (
            registration_search_page.registration_card_contributor_links
        )
        card_contributor_names = [
            el.text.strip().rstrip(',').strip() for el in card_contributor_elements
        ]
        has_more_contributors = (
            registration_search_page.registration_card_contributors_more.present()
        )
        more_count = 0
        if has_more_contributors:
            more_text = (
                registration_search_page.registration_card_contributors_more.text
            )
            match = re.search(r'\d+', more_text)
            more_count = int(match.group()) if match else 0

        # Collect information from first search result
        search_card_title = registration_search_page.registration_title.text
        dates = registration_search_page.registration_dates.text.split('|')
        search_card_reg_date = dates[0].replace('Date registered:', '').strip()

        # Expand secondary metadata dropdown on search card
        registration_search_page.secondary_metadata_dropdown.click()
        WebDriverWait(driver, 20).until(
            EC.text_to_be_present_in_element(
                (
                    By.CSS_SELECTOR,
                    'osf-resource-card:first-of-type osf-registration-secondary-metadata',
                ),
                'URL',
            )
        )

        # Get provider, registration template, and URL from the search card
        search_card_provider = (
            registration_search_page.registration_provider.text.split('Provider:')[
                1
            ].strip()
        )
        search_card_template = (
            registration_search_page.registration_template.text.split(
                'Registration Template:'
            )[1].strip()
        )
        search_card_url = registration_search_page.registration_url.text.split('URL:')[
            1
        ].strip()

        # Check if license is displayed on the search card
        has_license_on_card = registration_search_page.registration_license.present()
        if has_license_on_card:
            search_card_license = (
                registration_search_page.registration_license.text.split('License:')[
                    1
                ].strip()
            )

        # Check if DOI is displayed on the search card
        has_doi_on_card = registration_search_page.registration_doi.present()
        if has_doi_on_card:
            search_card_doi = registration_search_page.registration_doi.text.split(
                'DOI:'
            )[1].strip()

        # Wait for metadata to fully load before clicking on the title to avoid stale element reference error
        registration_search_page.registration_title.click_expecting_popup()
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'osf-registration-blocks-data')
            )
        )
        wait_until_page_ready(driver)

        # Wait for the right-hand metadata panel to finish rendering before reading
        # any of its fields (it loads asynchronously after the left-side summary block)
        WebDriverWait(driver, 15).until(
            lambda d: d.find_element(
                By.XPATH, '//h3[normalize-space()="Registry"]/following-sibling::p'
            ).text.strip()
            != ''
        )

        # Collect information from registration overview page
        reg_detail = RegistrationDetailPage(driver)
        reg_title = reg_detail.title.element.text
        registered_date = reg_detail.registered_date.text

        assert search_card_title == reg_title
        assert normalize_ui_date(search_card_reg_date) == normalize_ui_date(
            registered_date
        )
        assert search_card_provider == reg_detail.overview_registry.text
        assert search_card_template == reg_detail.overview_registration_type.text
        assert search_card_url in driver.current_url
        if has_license_on_card:
            assert search_card_license == reg_detail.overview_license.text
        if has_doi_on_card:
            detail_doi = reg_detail.registration_doi.text
            assert detail_doi in search_card_doi

        # Wait for osf-contributors-list to finish rendering before reading.
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[data-test-contributor-name]')
                )
            )
        except TimeoutException:
            pass  # Genuinely no contributors on this registration

        detail_contributor_names = [
            el.text.strip().rstrip(',').strip() for el in reg_detail.all_contributors
        ]

        try:
            total_on_detail = len(detail_contributor_names)
            if total_on_detail == 0:
                assert len(card_contributor_names) == 0
                assert not has_more_contributors
            elif total_on_detail <= 4:
                # Use sorted() because display order may differ between card and detail.
                assert sorted(card_contributor_names) == sorted(
                    detail_contributor_names
                )
                assert not has_more_contributors
            else:
                # 5+ contributors: a subset shown by name, rest as "and X more".
                # Use sets for the membership check (handles duplicate display names).
                card_name_set = set(card_contributor_names)
                detail_name_set = set(detail_contributor_names)
                assert card_name_set.issubset(
                    detail_name_set
                ), f'Card contributors {card_name_set} are not all present on detail page {detail_name_set}'
                assert has_more_contributors
                assert more_count == total_on_detail - len(card_contributor_names)
        except AssertionError:
            print(f'\nRegistration URL: {driver.current_url}')
            raise

    def test_sorting_by_created_date_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_sorting_by_created_date(driver, 'registered')

    def test_sorting_by_modified_date_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_sorting_by_modified_date(driver)

    def test_search_in_filtering_by_creator_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Creator menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.creator_dropdown_menu_selector
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.additional_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_date_created_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Date Created menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.date_created_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.date_created_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_funder_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Funder menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.funder_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.funder_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_subject_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Subject menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.subject_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.subject_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_license_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand License menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.license_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.license_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_resource_type_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Resource Type menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.resource_type_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.resource_type_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_institution_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Institution menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.institution_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.institution_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_community_schema_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Part of Community schema menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.includes_community_schema_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.includes_community_schema_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_provider_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Provider menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.provider_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.provider_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_registration_template_on_registrations_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.registrations_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand registration template menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.registration_template_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.registration_template_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)


class TestSearchPageFilesTab(SearchPageBase):
    def test_filtering_by_date_created_on_files_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open files tab
        search_page_short.files_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_date_created(driver, 'Date created')

    def test_filtering_by_funder_on_files_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open files tab
        search_page_short.files_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_funder(driver)

    def test_filtering_by_license_on_files_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open files tab
        search_page_short.files_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_license(driver)

    def test_filtering_by_resource_type_on_files_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open files tab
        base_page = BasePage(driver)
        search_page_short.files_tab_link.click()
        wait_until_page_ready(driver)

        wait = WebDriverWait(driver, 15)

        # 1. Expand Resource Type menu
        resource_type_menu = wait.until(
            EC.presence_of_element_located(search_page_short.resource_type_menu_locator)
        )
        base_page.scroll_to(resource_type_menu)

        resource_type_menu.click()

        # Click 'Select Resource Type' drop-down menu
        resource_type_multiselect_dropdown = wait.until(
            EC.visibility_of_element_located(
                search_page_short.resource_type_multiselect_dropdown_selector
            )
        )
        resource_type_multiselect_dropdown.click()
        wait_until_page_ready(driver)

        input_filed_locator = (
            By.XPATH,
            "//input[@role='searchbox' and contains(@class,'p-multiselect-filter')]",
        )

        wait.until(EC.visibility_of_element_located(input_filed_locator)).send_keys(
            'Book'
        )
        wait_until_page_ready(driver)

        # Save number of records related to the selected Resource Type
        number_of_records = search_page_short.get_record_count(driver, '1')

        # Select First option from the list
        wait_until_page_ready(driver)
        resource_type_first_option_locator = (
            By.XPATH,
            '(//ul[@role="listbox"]//li[@role="option"]//input[@type="checkbox"])[1]',
        )

        wait.until(
            EC.presence_of_element_located(resource_type_first_option_locator)
        ).click()

        wait_until_page_ready(driver)

        # CHeck if results displays correct number of results.
        result_count_after_filter_applying = search_page_short.get_results_count(driver)
        assert result_count_after_filter_applying <= number_of_records

        # Expand addition menu of the firs card
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.chevron_menu_first_card_locator
            )
        ).click()
        wait_until_page_ready(driver)
        # Check if cards in filtering results contains correct 'Resource Type'.

        resource_type_in_card_locator = (
            By.XPATH,
            "(//p[contains(normalize-space(),'Resource type:')])[1]",
        )

        element = wait.until(
            EC.visibility_of_element_located(resource_type_in_card_locator)
        )

        assert 'Book' in element.text

    def test_filtering_by_includes_community_on_files_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_short.files_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_includes_community_schema(driver)

    def test_clearing_of_applied_filters_on_files_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open files tab
        search_page_short.files_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_clearing_of_applied_filters(driver)

    def test_sorting_by_created_date_on_files_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Switch to the Files Tab
        search_page_short.files_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_sorting_by_created_date(driver, 'created')

    def test_sorting_by_modified_date_on_files_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Switch to the Files Tab
        search_page_short.files_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_sorting_by_modified_date(driver)

    def test_search_card_files(self, driver, file_search_page):
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
        )
        assert len(file_search_page.search_results) > 0

        # Grab the file information from the search card
        search_card_title = file_search_page.file_title.text.strip()
        from_href = file_search_page.from_project_link.get_attribute('href')
        parent_project_guid = from_href.rstrip('/').split('/')[-1]

        # Expand secondary metadata and check for funder info
        search_page = SearchPage(driver)
        wait = WebDriverWait(driver, 20)
        wait.until(
            EC.visibility_of_element_located(
                search_page.chevron_menu_first_card_locator
            )
        ).click()
        try:
            search_card_funder = file_search_page.funder_link.text.strip()
        except ValueError:
            search_card_funder = None

        file_search_page.file_title.click_expecting_popup()
        wait_until_page_ready(driver)

        # Files attached to preprints navigate to the preprint page rather
        # than a dedicated file detail page — skip rather than fail.
        if '/preprints/' in driver.current_url:
            pytest.skip(
                'File belongs to a preprint — navigates to preprint page, not file detail'
            )

        # Verify the file detail page title matches the search card title
        file_detail_page = FileDetailPage(driver)
        file_detail_title = file_detail_page.file_title.text.strip()
        assert search_card_title == file_detail_title

        # Verify the parent project guid appears in the files page breadcrumbs
        breadcrumb_text = file_detail_page.breadcrumbs.text.lower()
        assert parent_project_guid in breadcrumb_text

        # Only check for funder if present
        if search_card_funder:
            detail_funder = file_detail_page.funder.text.strip()
            assert search_card_funder == detail_funder

    def test_search_in_filtering_by_date_created_on_files_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Switch to the Files Tab
        search_page_short.files_tab_link.click()

        # 1. Expand Date Created menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.date_created_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.date_created_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_funder_on_files_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Switch to the Files Tab
        search_page_short.files_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Funder menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.funder_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.funder_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_license_on_files_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Switch to the Files Tab
        search_page_short.files_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand License menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.license_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.license_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_community_schema_on_files_tab(
        self, driver, search_page_short
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Switch to the Files Tab
        search_page_short.files_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Part of Community schema menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.includes_community_schema_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.includes_community_schema_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_resource_type_on_files_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Switch to the Files Tab
        search_page_short.files_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Resource Type menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.resource_type_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.resource_type_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)


class TestSearchPageProjectsTab(SearchPageBase):
    @pytest.mark.skip(reason='ENG-10674')
    def test_filtering_by_creator_on_projects_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_creator(driver)

    def test_filtering_by_date_created_on_projects_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_date_created(driver, 'Date created')

    @pytest.mark.skip(reason='ENG-10674')
    def test_filtering_by_funder_on_projects_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_funder(driver)

    @pytest.mark.skip(reason='ENG-10674')
    def test_filtering_by_subject_on_projects_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_subject(driver)

    def test_filtering_by_license_on_projects_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_license(driver)

    def test_filtering_by_institution_on_projects_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_institution(driver)

    @pytest.mark.skip(reason='ENG-10674')
    def test_filtering_by_part_of_collection_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_part_of_collection(driver)

    @pytest.mark.skip(reason='ENG-10674')
    def test_filtering_by_includes_community_schema_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_filtering_by_includes_community_schema(driver)

    def test_filtering_by_associated_preprint_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 25)
        base_page = BasePage(driver)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Additional Filters menu
        additional_filters_menu = wait.until(
            EC.visibility_of_element_located(
                search_page_short.additional_filters_menu_locator
            )
        )
        additional_filters_menu.click()

        # Select additional option from the list
        additional_option_locator = (By.XPATH, "//input[@id='checkbox-supplements']")

        # skip tests if testing data is missing
        try:
            wait.until(EC.presence_of_element_located(additional_option_locator))
        except TimeoutException:
            pytest.skip('Record was not found in the list')

        additional_option = wait.until(
            EC.presence_of_element_located(additional_option_locator)
        )
        base_page.scroll_to(additional_option)

        # Save number of records related to the selected additional option
        number_of_records = search_page_short.get_record_count_for_additional_filters(
            driver, 'Associated preprint'
        )

        # Select additional option from the list
        wait.until(EC.presence_of_element_located(additional_option_locator)).click()
        wait_until_page_ready(driver)

        # CHeck if results displays correct number of results.
        result_count_after_filter_applying = search_page_short.get_results_count(driver)
        assert result_count_after_filter_applying <= number_of_records

        # Click on the title os the first element in search results
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.first_search_result_title_locator
            )
        ).click()

        # Switch to the second tab
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])

        # Check if page  contains selected option
        wait_until_page_ready(driver)
        locator = (By.XPATH, "//osf-overview-supplements//p[contains(., 'Preprints')]")

        assert wait.until(EC.visibility_of_element_located(locator))

    def test_clearing_of_applied_filters_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_clearing_of_applied_filters(driver)

    @pytest.mark.skip(reason='ENG-10674')
    def test_filtering_by_resource_type_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        base_page = BasePage(driver)
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        wait = WebDriverWait(driver, 15)

        # 1. Expand Resource Type menu
        resource_type_menu = wait.until(
            EC.presence_of_element_located(search_page_short.resource_type_menu_locator)
        )
        base_page.scroll_to(resource_type_menu)

        resource_type_menu.click()

        # Click 'Select Resource Type' drop-down menu
        resource_type_multiselect_dropdown = wait.until(
            EC.visibility_of_element_located(
                search_page_short.resource_type_multiselect_dropdown_selector
            )
        )
        resource_type_multiselect_dropdown.click()
        wait_until_page_ready(driver)

        input_filed_locator = (
            By.XPATH,
            "//input[@role='searchbox' and contains(@class,'p-multiselect-filter')]",
        )

        wait.until(EC.visibility_of_element_located(input_filed_locator)).send_keys(
            'Book'
        )
        wait_until_page_ready(driver)

        # Save number of records related to the selected Resource Type
        number_of_records = search_page_short.get_record_count(driver, '1')

        # Select First option from the list
        wait_until_page_ready(driver)
        resource_type_first_option_locator = (
            By.XPATH,
            '(//ul[@role="listbox"]//li[@role="option"]//input[@type="checkbox"])[1]',
        )

        wait.until(
            EC.presence_of_element_located(resource_type_first_option_locator)
        ).click()

        wait_until_page_ready(driver)

        # CHeck if results displays correct number of results.
        result_count_after_filter_applying = search_page_short.get_results_count(driver)
        assert result_count_after_filter_applying == number_of_records

        # Expand addition menu of the firs card
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.chevron_menu_first_card_locator
            )
        ).click()
        wait_until_page_ready(driver)
        # Check if cards in filtering results contains correct 'Resource Type'.

        resource_type_in_card_locator = (
            By.XPATH,
            "(//p[contains(normalize-space(),'Resource type:')])[1]",
        )

        element = wait.until(
            EC.visibility_of_element_located(resource_type_in_card_locator)
        )

        assert 'Book' in element.text

    def test_sorting_by_created_date_on_projects_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # search_page_short.loading_indicator.here_then_gone()
        # Switch to the Projects Tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_sorting_by_created_date(driver, 'created')

    def test_sorting_by_modified_date_on_projects_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        # search_page.loading_indicator.here_then_gone()
        # Switch to the Projects Tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_sorting_by_modified_date(driver)

    def test_search_in_filtering_by_creator_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Creator menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.creator_dropdown_menu_selector
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.additional_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_date_created_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Date Created menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.date_created_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.date_created_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_funder_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Funder menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.funder_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.funder_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_subject_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Subject menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.subject_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.subject_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_license_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand License menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.license_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.license_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_resource_type_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Resource Type menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.resource_type_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.resource_type_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_institution_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Institution menu
        wait.until(
            EC.visibility_of_element_located(search_page_short.institution_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.institution_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_part_of_collection_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Part of Collection menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.part_of_collection_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.part_of_collection_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_community_schema_on_projects_tab(
        self, driver, search_page_short
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Open projects tab
        search_page_short.projects_tab_link.click()
        wait_until_page_ready(driver)

        # 1. Expand Part of Community schema menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.includes_community_schema_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_short.includes_community_schema_multiselect_dropdown_selector
            )
        ).click()

        search_page_short.check_search_in_filtering_options(driver)

    def test_search_card_projects(self, driver, project_search_page):
        WebDriverWait(driver, 25).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
        )

        assert len(project_search_page.search_results) > 0

        for _ in range(3):
            if project_search_page.first_card_type.text != 'Project Component':
                break
            driver.refresh()
            WebDriverWait(driver, 25).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
            )
        else:
            # Project component actually navigates to the parent project, which may have different contributors.
            pytest.skip('Project component skipped')

        # Collect project information from search card
        project_title = project_search_page.project_title.text
        dates = project_search_page.project_dates.text.split('|')
        search_card_date_created = dates[0].replace('Date created:', '').strip()

        project_search_page.secondary_metadata_dropdown.click()
        WebDriverWait(driver, 20).until(
            EC.text_to_be_present_in_element(
                (
                    By.CSS_SELECTOR,
                    'osf-resource-card:first-of-type osf-project-secondary-metadata',
                ),
                'URL',
            )
        )

        # Check if license is displayed on the search card
        has_license_on_card = project_search_page.project_license.present()
        if has_license_on_card:
            search_card_license = project_search_page.project_license.text.split(
                'License:'
            )[1].strip()

        # Check if DOI is displayed on the search card
        has_doi_on_card = project_search_page.project_doi.present()
        if has_doi_on_card:
            search_card_doi = project_search_page.project_doi.text.split('DOI:')[
                1
            ].strip()

        # Check if collection is displayed on the search card
        has_collection_on_card = project_search_page.project_collection.present()
        if has_collection_on_card:
            search_card_collection = project_search_page.project_collection.text.split(
                'Collection:'
            )[1].strip()

        # Collect contributors from search card
        # card_contributor_elements = project_search_page.project_card_contributor_links
        # card_contributor_names = [
        #     el.text.strip().rstrip(',').strip() for el in card_contributor_elements
        # ]
        # has_more_contributors = project_search_page.project_card_contributors_more.present()
        # more_count = 0
        # if has_more_contributors:
        #     more_text = project_search_page.project_card_contributors_more.text
        #     match = re.search(r'\d+', more_text)
        #     more_count = int(match.group()) if match else 0

        project_search_page.project_title.click_expecting_popup()
        WebDriverWait(driver, 25).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'h1.flex.align-items-center')
            )
        )
        wait_until_page_ready(driver)

        # Collect information from project detail page
        project_detail = ProjectPage(driver)
        project_detail_title = project_detail.title.element.text
        project_detail_date_created = project_detail.date_created.text
        project_detail_license = project_detail.license.text

        # Wait for osf-contributors-list to finish rendering — the h3 appears before
        # the async child component populates its links, so wait for actual <a> elements
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//h3[normalize-space()="Contributors"]'
                        '/following-sibling::div//a',
                    )
                )
            )
        except TimeoutException:
            pass  # Genuinely no contributors on this project

        print(f'\nProject URL: {driver.current_url}')

        assert project_title == project_detail_title
        assert normalize_ui_date(search_card_date_created) == normalize_ui_date(
            project_detail_date_created
        )
        if has_license_on_card:
            assert search_card_license == project_detail_license
        else:
            assert project_detail_license == 'No License'
        if has_collection_on_card:
            project_detail_collection = project_detail.collection.text
            assert search_card_collection in project_detail_collection
        else:
            assert 'No collections' in project_detail.collection.text
        if has_doi_on_card:
            project_detail_doi = project_detail.doi.text
            assert project_detail_doi in search_card_doi

        # Verify contributors match between search card and detail page
        # pytest.xfail(
        #     'ENG-10XXX: Search card does not consistently display all contributors'
        # )
        # total_on_detail = len(detail_unique_names)
        # if total_on_detail == 0:
        #     # Case 1: No contributors
        #     assert len(card_contributor_names) == 0
        #     assert not has_more_contributors
        # elif total_on_detail <= 4:
        #     # Case 2: 1–4 contributors, all shown on card
        #     assert card_contributor_names == detail_unique_names
        #     assert not has_more_contributors
        # else:
        #     # Case 3: 5+ contributors — first 4 by name, rest as "and X more"
        #     assert card_contributor_names == detail_unique_names[:4]
        #     assert has_more_contributors
        #     assert more_count == total_on_detail - 4


class TestSearchPageUsersTab(SearchPageBase):
    def test_sorting_by_created_date_on_users_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        search_page_short.loading_indicator.here_then_gone()
        # Switch to the Users Tab
        search_page_short.users_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_sorting_by_created_date(driver, 'created')

    def test_sorting_by_modified_date_on_users_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        search_page_short.loading_indicator.here_then_gone()
        # Switch to the Users Tab
        search_page_short.users_tab_link.click()
        wait_until_page_ready(driver)

        search_page_short.check_sorting_by_modified_date(driver)

    def test_search_results_exist_users_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        search_page_short.loading_indicator.here_then_gone()
        # Switch to the Users Tab
        search_page_short.users_tab_link.click()
        search_page_short.loading_indicator.here_then_gone()
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
            )
        )
        assert len(search_page_short.search_results) > 0
        # Verify that first search result is of User type
        assert search_page_short.first_card_object_type_label.text == 'User'

    def test_filtering_on_users_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        search_page_short.loading_indicator.here_then_gone()
        # Switch to the Users Tab
        search_page_short.users_tab_link.click()
        search_page_short.loading_indicator.here_then_gone()
        wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
            )
        )

        # 1. Expand Institution menu
        institution_menu = wait.until(
            EC.visibility_of_element_located(
                search_page_short.institution_menu_selector
            )
        )
        institution_menu.click()

        # Click 'Select institution' drop-down menu
        institution_multiselect_dropdown = wait.until(
            EC.visibility_of_element_located(
                search_page_short.additional_multiselect_dropdown_selector
            )
        )
        institution_multiselect_dropdown.click()

        institution_first_option_locator = (
            By.XPATH,
            '(//ul[@role="listbox"]//li[@role="option"])[1]',
        )
        # Save name of the selected institution
        name_of_institution = search_page_short.get_record_name(driver, '1')

        # Save number of users related to the institution.
        number_of_users = search_page_short.get_record_count(driver, '1')

        # Select First institution from the list
        wait.until(
            EC.visibility_of_element_located(institution_first_option_locator)
        ).click()
        wait_until_page_ready(driver)

        # CHeck if results displays correct number of users.
        result_count_after_filter_applying = search_page_short.get_results_count(driver)
        assert result_count_after_filter_applying == number_of_users

        # Check if cards in filtering results contains name of institution.
        institution_locator = (
            By.XPATH,
            f'//p-accordion-panel//a[contains(normalize-space(), "{name_of_institution}")]',
        )

        element = wait.until(EC.visibility_of_element_located(institution_locator))

        assert element.is_displayed()

    def test_clearing_of_applied_filters_on_users_tab(self, driver, search_page_short):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        search_page_short.loading_indicator.here_then_gone()
        # Switch to the Users Tab
        search_page_short.users_tab_link.click()
        search_page_short.loading_indicator.here_then_gone()
        wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
            )
        )
        # save number of results without filters
        result_count_without_filter = search_page_short.get_results_count(driver)

        #
        # 1. Expand Institution menu
        institution_menu = wait.until(
            EC.visibility_of_element_located(
                search_page_short.institution_menu_selector
            )
        )
        institution_menu.click()

        # Click 'Select institution' drop-down menu
        institution_multiselect_dropdown = wait.until(
            EC.visibility_of_element_located((By.ID, 'any-of'))
        )
        institution_multiselect_dropdown.click()

        # Select First institution from the list
        first_option_locator = (
            By.XPATH,
            '(//ul[@role="listbox"]//li[@role="option"])[1]',
        )

        wait.until(EC.element_to_be_clickable(first_option_locator)).click()

        #
        wait_until_page_ready(driver)

        # Check that number of results is changes
        result_count_after_filter_applying = search_page_short.get_results_count(driver)
        assert result_count_after_filter_applying != result_count_without_filter

        # Clear applied filter.
        remove_button_locator = (By.CSS_SELECTOR, 'span.p-chip-remove-icon')

        wait.until(EC.element_to_be_clickable(remove_button_locator)).click()

        # Check that initial numbers of result is the same that displayed
        wait_until_page_ready(driver)
        result_count_after_removing_filter = search_page_short.get_results_count(driver)
        assert result_count_without_filter == result_count_after_removing_filter

    def test_search_card_users(self, driver, user_search_page):
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
        )
        assert len(user_search_page.search_results) > 0

        # Collect user information from the search card
        search_card_name = user_search_page.user_name.text.strip()
        has_orcid = user_search_page.orcid_badge.present()

        # Expand the accordion to reveal secondary metadata
        user_search_page.secondary_metadata_dropdown.click()
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element(
                (
                    By.CSS_SELECTOR,
                    'osf-resource-card:first-of-type osf-user-secondary-metadata',
                ),
                'Public projects',
            )
        )

        # Collect secondary metadata counts from the first search card
        public_projects = int(
            user_search_page.user_public_projects.text.split(':')[1].strip()
        )
        public_registrations = int(
            user_search_page.user_public_registrations.text.split(':')[1].strip()
        )
        public_preprints = int(
            user_search_page.user_public_preprints.text.split(':')[1].strip()
        )

        # Click user name link to navigate to profile page
        user_search_page.user_name.click_expecting_popup()
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'osf-profile-information')
            )
        )

        # Verify the profile page name matches the search card name
        profile_page = UserProfilePage(driver)
        profile_name = profile_page.profile_name.text.strip()
        assert search_card_name == profile_name
        if has_orcid:
            assert profile_page.orcid_link.present()

        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'p-progress-spinner'))
        )

        # Verify Projects count
        if public_projects > 0:
            profile_page.projects_tab.click()
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, 'p-progress-spinner')
                )
            )
            WebDriverWait(driver, 15).until(
                EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, 'p.type.py-1.px-3.font-bold'), 'Project'
                )
            )
            result_text = profile_page.result_count.text.strip()
            profile_projects = int(result_text.split()[0])
            # note: projects marked as 'spam' are not counted on the user profile page
            assert public_projects >= profile_projects

        # Verify Registrations count
        if public_registrations > 0:
            profile_page.registrations_tab.click()
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, 'p-progress-spinner')
                )
            )
            WebDriverWait(driver, 15).until(
                EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, 'p.type.py-1.px-3.font-bold'),
                    'Registration',
                )
            )
            result_text = profile_page.result_count.text.strip()
            profile_registrations = int(result_text.split()[0])
            # note: withdrawn registrations are not counted on the user profile page
            assert public_registrations >= profile_registrations

        # Verify Preprints count
        if public_preprints > 0:
            profile_page.preprints_tab.click()
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, 'p-progress-spinner')
                )
            )
            WebDriverWait(driver, 15).until(
                EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, 'p.type.py-1.px-3.font-bold'), 'Preprint'
                )
            )
            result_text = profile_page.result_count.text.strip()
            profile_preprints = int(result_text.split()[0])
            # note: withdrawn preprints are not counted on the user profile page
            assert public_preprints >= profile_preprints
