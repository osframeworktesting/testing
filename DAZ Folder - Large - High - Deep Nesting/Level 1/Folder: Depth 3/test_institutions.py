import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import markers
from api import osf_api

# from pages.base import BasePage
from pages.institutions import (
    InstitutionAdminDashboardPage,
    InstitutionBrandedPage,
    InstitutionsLandingPage,
)
from pages.search import (
    FileSearchResults,
    PreprintSearchResults,
    ProjectSearchResults,
    RegistrationSearchResults,
    SearchPage,
    SearchPageHelpers,
    UserSearchResults,
)

# from pages.user import UserProfilePage
# from tests.test_profile import (
#     _validate_file_card,
#     _validate_preprint_card,
#     _validate_project_card,
#     _validate_registration_card,
# )
from utils import wait_until_page_ready


def normalize_ui_date(date_string):
    try:
        # The date from the search card is formatted (February 17, 2026)
        return datetime.strptime(date_string, '%B %d, %Y').date()
    except ValueError:
        # Registration overview page date is formatted (Feb 17, 2026, 10:51 AM)
        dt = datetime.strptime(date_string, '%b %d, %Y, %I:%M %p')
        dt = dt.replace(tzinfo=ZoneInfo('America/New_York'))
        return dt.astimezone(ZoneInfo('UTC')).date()


@pytest.fixture()
def search_page(driver):
    search_page = SearchPage(driver)
    search_page.goto()
    return search_page


@pytest.fixture()
def search_page_short(driver):
    search_page = SearchPageHelpers(driver)
    # search_page.goto_short()
    return search_page


@pytest.fixture()
def registration_search_page(driver):
    reg_search_page = RegistrationSearchResults(driver)
    # reg_search_page.goto_short()
    return reg_search_page


@pytest.fixture()
def preprint_search_page(driver):
    preprint_search_page = PreprintSearchResults(driver)
    # preprint_search_page.goto()
    return preprint_search_page


@pytest.fixture()
def project_search_page(driver):
    project_search_page = ProjectSearchResults(driver)
    # project_search_page.goto()
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


@pytest.fixture()
def institution_page(driver):
    landing_page = InstitutionsLandingPage(driver)
    landing_page.goto_short()
    return landing_page


def select_institution(driver, institution_page, institution_name):
    search_input = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable(institution_page.search_bar_locator)
    )

    search_input.clear()
    search_input.send_keys(institution_name)

    institution_locator = (
        By.XPATH,
        f"//div[contains(@class,'border-round-xl') and .//h2[contains(text(),'{institution_name}')]]",
    )

    institution = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(institution_locator)
    )

    driver.execute_script('arguments[0].click();', institution)


@markers.smoke_test
@markers.core_functionality
@pytest.mark.usefixtures('throttle_on_prod')
class TestInstitutionsPage:
    @pytest.fixture()
    def landing_page(self, driver):
        landing_page = InstitutionsLandingPage(driver)
        landing_page.goto()
        return landing_page

    def test_select_institution(self, driver, landing_page):
        landing_page.institution_list[0].click()
        assert InstitutionBrandedPage(driver, verify=True)

    def test_filter_by_institution(
        self,
        driver,
        institution_page,
        search_page_short,
        institution='Center For Open Science',
    ):
        wait_until_page_ready(driver)
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(institution_page.search_bar_locator)
        ).send_keys(f'{institution}')
        search_page_short.loading_indicator.here_then_gone()

        wait_until_page_ready(driver)

        assert institution in institution_page.institution_list[0].text


@markers.dont_run_on_prod
@markers.core_functionality
# Can't run this is Production since we don't have admin access to any institutions in
# Production
class TestInstitutionAdminDashboardPage:
    def wait_until_page_ready(self, driver, timeout=30):
        wait = WebDriverWait(driver, timeout)

        wait.until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'p-progress-spinner'))
        )

    def test_institution_admin_dashboard(self, driver, session, must_be_logged_in):
        """Test using the COS admin dashboard page - user must already be setup as an
        admin for the COS institution in each environment through the OSF admin app.
        """
        dashboard_page = InstitutionAdminDashboardPage(driver, institution_id='cos')
        dashboard_page.goto()
        assert InstitutionAdminDashboardPage(driver, verify=True)
        dashboard_page.loading_indicator.here_then_gone()
        # Select 'QA' from Departments listbox and verify that the correct number
        # of users are displayed in the table
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//p-tab[normalize-space(text())='Users']")
            )
        )
        driver.find_element(
            By.XPATH, "//p-tab[normalize-space(text())='Users']"
        ).click()
        self.wait_until_page_ready(driver)

        dashboard_page.all_departments_dropdown.click()

        self.wait_until_page_ready(driver)
        driver.find_element(
            By.XPATH, "//li[@role='option' and normalize-space(.)='QA']"
        ).click()
        self.wait_until_page_ready(driver)

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//td[.//p[normalize-space()='QA']]")
            )
        )
        user_table_rows = len(
            driver.find_elements(By.XPATH, "//td[.//p[normalize-space()='QA']]")
        )
        api_qa_users = osf_api.get_institution_users_per_department(
            session, institution_id='cos', department='QA'
        )
        assert user_table_rows == len(api_qa_users)

        # Get metrics data using the OSF api

        metrics_data = osf_api.get_institution_metrics_summary(
            session, institution_id='cos'
        )
        api_public_project_count = metrics_data['attributes']['public_project_count']
        api_private_project_count = metrics_data['attributes']['private_project_count']

        # Verify Total User Count
        # !!!!!BELOW ROW COMMENTED because of issue with counting of the total users.
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//p-tab[normalize-space(text())='Summary']")
            )
        ).click()

        self.wait_until_page_ready(driver)
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//p[normalize-space()='OSF Public and Private Projects']/preceding::h2[1]",
                )
            )
        )
        total_displayed_projects_count = int(
            driver.find_element(
                By.XPATH,
                "//p[normalize-space()='OSF Public and Private Projects']/preceding::h2[1]",
            ).text
        )
        dashboard_page.click_on_listbox_trigger('Public vs Private Projects')

        # Verify Public Project Count
        projects_chevron = driver.find_element(
            By.XPATH,
            "//p-accordion-header[.//p[normalize-space()='Public vs Private Projects']]",
        )
        driver.execute_script('arguments[0].scrollIntoView(true);', projects_chevron)
        self.wait_until_page_ready(driver)
        projects_chevron.click()
        time.sleep(3)

        displayed_public_project_elem = driver.find_elements(
            By.XPATH,
            "//li[.//span[normalize-space()='Public projects:']]//span[last()]",
        )

        displayed_public_project_count = int(displayed_public_project_elem[1].text)
        assert int(displayed_public_project_count) == api_public_project_count

        # Verify Private Project Count
        displayed_private_project_elem = driver.find_elements(
            By.XPATH,
            "//li[.//span[normalize-space()='Private projects']]//span[last()]",
        )
        displayed_private_project_count = int(displayed_private_project_elem[1].text)
        assert int(displayed_private_project_count) == api_private_project_count

        # Verify Total Project Count
        assert (
            total_displayed_projects_count
            == api_public_project_count + api_private_project_count
        )


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


# @markers.smoke_test
# @markers.core_functionality
# @pytest.mark.usefixtures('throttle_on_prod')
# class TestInstitutionPageSearch:
#     def test_search_results_exist_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         search_page_short.search_input.send_keys('test')
#         search_page_short.search_input.send_keys(Keys.ENTER)
#         search_page_short.loading_indicator.here_then_gone()
#         WebDriverWait(driver, 15).until(
#             EC.visibility_of_element_located(
#                 (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
#             )
#         )
#         assert len(search_page_short.search_results) > 0
#
#     def test_search_results_exist_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#         search_page_short.search_input.send_keys('test')
#         search_page_short.search_input.send_keys(Keys.ENTER)
#         search_page_short.loading_indicator.here_then_gone()
#         # Switch to the Projects Tab
#         search_page_short.projects_tab_link.click()
#         search_page_short.loading_indicator.here_then_gone()
#         WebDriverWait(driver, 15).until(
#             EC.visibility_of_element_located(
#                 (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
#             )
#         )
#         assert len(search_page_short.search_results) > 0
#         # Verify that first search result is of Project type
#         assert search_page_short.first_card_object_type_label.text[:7] == 'Project'
#
#     def test_search_results_exist_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#         search_page_short.search_input.send_keys('test')
#         search_page_short.search_input.send_keys(Keys.ENTER)
#         search_page_short.loading_indicator.here_then_gone()
#         # Switch to the Registrations Tab
#         search_page_short.registrations_tab_link.click()
#         search_page_short.loading_indicator.here_then_gone()
#         WebDriverWait(driver, 15).until(
#             EC.visibility_of_element_located(
#                 (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
#             )
#         )
#         assert len(search_page_short.search_results) > 0
#         # Verify that first search result is of Registration type
#         assert (
#             search_page_short.first_card_object_type_label.text[:12] == 'Registration'
#         )
#
#     def test_search_results_exist_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#         search_page_short.search_input.send_keys('test')
#         search_page_short.search_input.send_keys(Keys.ENTER)
#         search_page_short.loading_indicator.here_then_gone()
#         # Switch to the Preprints Tab
#         search_page_short.preprints_tab_link.click()
#         search_page_short.loading_indicator.here_then_gone()
#         WebDriverWait(driver, 15).until(
#             EC.visibility_of_element_located(
#                 (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
#             )
#         )
#         assert len(search_page_short.search_results) > 0
#         # Verify that first search result is of Preprint type
#         assert search_page_short.first_card_object_type_label.text == 'Preprint'
#
#     def test_search_results_exist_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open files tab
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#         search_page_short.search_input.send_keys('test')
#         search_page_short.search_input.send_keys(Keys.ENTER)
#         search_page_short.loading_indicator.here_then_gone()
#         # Switch to the Files Tab
#         search_page_short.files_tab_link.click()
#         search_page_short.loading_indicator.here_then_gone()
#         WebDriverWait(driver, 15).until(
#             EC.visibility_of_element_located(
#                 (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
#             )
#         )
#         assert len(search_page_short.search_results) > 0
#         # Verify that first search result is of File type
#         assert search_page_short.first_card_object_type_label.text == 'File'
#
#
# class TestInstitutionsPageSearchAllTab:
#
#     # @pytest.mark.skip(reason='ENG-10674')
#     def test_filtering_by_creator_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         search_page_short.check_filtering_by_creator(driver)
#
#     def test_filtering_by_date_created_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         search_page_short.check_filtering_by_date_created(driver, 'Date created')
#
#     # @pytest.mark.skip(reason='ENG-10674')
#     def test_filtering_by_funder_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         search_page_short.check_filtering_by_funder(driver)
#
#     def test_filtering_by_subject_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         search_page_short.check_filtering_by_subject(driver)
#
#     def test_filtering_by_license_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         search_page_short.check_filtering_by_license(driver)
#
#     def test_filtering_by_resource_type_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         base_page = BasePage(driver)
#         wait = WebDriverWait(driver, 15)
#
#         # 1. Expand Resource Type menu
#         resource_type_menu = wait.until(
#             EC.presence_of_element_located(search_page_short.resource_type_menu_locator)
#         )
#         base_page.scroll_to(resource_type_menu)
#
#         resource_type_menu.click()
#
#         # Click 'Select Resource Type' drop-down menu
#         resource_type_multiselect_dropdown = wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.resource_type_multiselect_dropdown_selector
#             )
#         )
#         resource_type_multiselect_dropdown.click()
#         wait_until_page_ready(driver)
#
#         input_filed_locator = (
#             By.XPATH,
#             "//input[@role='searchbox' and contains(@class,'p-multiselect-filter')]",
#         )
#         wait.until(EC.visibility_of_element_located(input_filed_locator)).send_keys(
#             'preprin'
#         )
#         wait_until_page_ready(driver)
#         # Save name of the selected option (Resource Type)
#         name_of_record = search_page_short.get_record_name(driver, '1')
#
#         # Save number of records related to the selected Resource Type
#         number_of_records = search_page_short.get_record_count(driver, '1')
#
#         # Select First option from the list
#         wait_until_page_ready(driver)
#         resource_type_first_option_locator = (
#             By.XPATH,
#             '(//ul[@role="listbox"]//li[@role="option"]//input[@type="checkbox"])[1]',
#         )
#
#         wait.until(
#             EC.presence_of_element_located(resource_type_first_option_locator)
#         ).click()
#
#         wait_until_page_ready(driver)
#
#         # CHeck if results displays correct number of results.
#         result_count_after_filter_applying = search_page_short.get_results_count(driver)
#         assert result_count_after_filter_applying <= number_of_records
#
#         # Check if cards in filtering results contains correct 'Resource Type'.
#
#         resource_type_in_card_locator = (
#             By.XPATH,
#             f"//p[contains(@class,'type') and normalize-space()='{name_of_record}']",
#         )
#
#         assert wait.until(
#             EC.presence_of_element_located(resource_type_in_card_locator)
#         ).is_displayed()
#
#     # @pytest.mark.skip(reason='ENG-10674')
#     def test_filtering_by_part_of_collection_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         base_page = BasePage(driver)
#         wait = WebDriverWait(driver, 15)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # 1. Expand "Is part of collection " menu
#         part_of_collection_menu = wait.until(
#             EC.presence_of_element_located(
#                 search_page_short.part_of_collection_menu_locator
#             )
#         )
#         base_page.scroll_to(part_of_collection_menu)
#
#         part_of_collection_menu.click()
#
#         # Click 'Select collection' drop-down menu
#         part_of_collection_multiselect_dropdown = wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.part_of_collection_multiselect_dropdown_selector
#             )
#         )
#         part_of_collection_multiselect_dropdown.click()
#
#         # Save name of the selected option (Collection)
#         name_of_record = search_page_short.get_record_name(driver, '1')
#
#         # Save number of records related to the selected Collection
#         number_of_records = search_page_short.get_record_count(driver, '1')
#
#         # Select First option from the list
#         wait_until_page_ready(driver)
#         collection_first_option_locator = (
#             By.XPATH,
#             '(//ul[@role="listbox"]//li[@role="option"]//input[@type="checkbox"])[1]',
#         )
#
#         wait.until(
#             EC.presence_of_element_located(collection_first_option_locator)
#         ).click()
#         wait_until_page_ready(driver)
#
#         # CHeck if results displays correct number of results.
#         result_count_after_filter_applying = search_page_short.get_results_count(driver)
#         assert result_count_after_filter_applying <= number_of_records
#
#         # Expand addition menu of the firs card
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.chevron_menu_first_card_locator
#             )
#         ).click()
#
#         # Check if cards in filtering results contains correct 'Collection'.
#         record_locator = (By.XPATH, "(//p[contains(., ' Collection: ')]//a)[1]")
#
#         element = wait.until(EC.presence_of_element_located(record_locator))
#         base_page.scroll_to(element)
#
#         assert name_of_record in element.text
#
#     def test_filtering_by_provider_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         base_page = BasePage(driver)
#         wait = WebDriverWait(driver, 15)
#
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # 1. Expand "Provider " menu
#         provider_menu = wait.until(
#             EC.presence_of_element_located(search_page_short.provider_menu_locator)
#         )
#         base_page.scroll_to(provider_menu)
#
#         provider_menu.click()
#
#         # Click 'Select provider' drop-down menu
#         provider_multiselect_dropdown = wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.provider_multiselect_dropdown_selector
#             )
#         )
#         provider_multiselect_dropdown.click()
#
#         input_filed_locator = (
#             By.XPATH,
#             "//input[@role='searchbox' and contains(@class,'p-multiselect-filter')]",
#         )
#         wait.until(EC.visibility_of_element_located(input_filed_locator)).send_keys(
#             'regis'
#         )
#         wait_until_page_ready(driver)
#
#         # Save name of the selected option (Provider)
#         name_of_record = search_page_short.get_record_name(driver, '1')
#
#         # Save number of records related to the selected Provider
#         number_of_records = search_page_short.get_record_count(driver, '1')
#
#         # Select First option from the list
#         wait_until_page_ready(driver)
#         provider_first_option_locator = (
#             By.XPATH,
#             '(//ul[@role="listbox"]//li[@role="option"]//input[@type="checkbox"])[1]',
#         )
#
#         wait.until(
#             EC.presence_of_element_located(provider_first_option_locator)
#         ).click()
#         wait_until_page_ready(driver)
#
#         # CHeck if results displays correct number of results.
#         result_count_after_filter_applying = search_page_short.get_results_count(driver)
#         assert result_count_after_filter_applying <= number_of_records
#
#         # Expand addition menu of the firs card
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.chevron_menu_first_card_locator
#             )
#         ).click()
#
#         # Check if cards in filtering results contains correct 'Provider'.
#
#         record_locator = (By.XPATH, "(//p[contains(., ' Provider: ')]//a)[1]")
#
#         element = wait.until(EC.presence_of_element_located(record_locator))
#         base_page.scroll_to(element)
#
#         assert name_of_record in element.text
#
#     def test_filtering_by_institution_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         search_page_short.check_filtering_by_institution(driver, '3')
#
#     def test_sorting_by_created_date_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         search_page_short.check_sorting_by_created_date(driver, 'created')
#
#     def test_sorting_by_modified_date_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         search_page_short.check_sorting_by_modified_date(driver)
#
#     def test_search_in_filtering_by_creator_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # 1. Expand Creator menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.creator_dropdown_menu_selector
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.additional_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_date_created_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # 1. Expand Date Created menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.date_created_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.date_created_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_funder_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # 1. Expand Funder menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.funder_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.funder_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_subject_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # 1. Expand Subject menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.subject_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.subject_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_license_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # 1. Expand License menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.license_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.license_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_resource_type_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # 1. Expand Resource Type menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.resource_type_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.resource_type_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_institution_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # 1. Expand Institution menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.institution_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.institution_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_provider_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # 1. Expand Provider menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.provider_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.provider_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver, '2')
#
#     def test_search_in_filtering_by_part_of_collection_on_all_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # 1. Expand Part of Collection menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.part_of_collection_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.part_of_collection_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_card_all(self, driver, institution_page, search_page_short):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         search_page_short.loading_indicator.here_then_gone()
#         wait_until_page_ready(driver)
#         WebDriverWait(driver, 25).until(
#             EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
#         )
#
#         search_page = SearchPage(driver)
#         assert len(search_page.search_results) > 0
#
#         result_type = search_page.node_type.text.strip()
#
#         dispatch = {
#             'Project': lambda: _validate_project_card(
#                 driver, ProjectSearchResults(driver)
#             ),
#             'Registration': lambda: _validate_registration_card(
#                 driver, RegistrationSearchResults(driver)
#             ),
#             'Preprint': lambda: _validate_preprint_card(
#                 driver, PreprintSearchResults(driver)
#             ),
#             'File': lambda: _validate_file_card(driver, FileSearchResults(driver)),
#         }
#
#         for attempt in range(3):
#             if result_type in dispatch:
#                 break
#             if attempt < 2:
#                 driver.refresh()
#                 WebDriverWait(driver, 25).until(
#                     EC.visibility_of_element_located(
#                         (By.CSS_SELECTOR, 'osf-resource-card')
#                     )
#                 )
#                 result_type = search_page.node_type.text.strip()
#         else:
#             pytest.fail(f'Unknown search result type: {result_type!r}')
#
#         dispatch[result_type]()
#
#
# class TestInstitutionsPagePreprintsTab:
#     def test_filtering_by_creator_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_creator(driver)
#
#     def test_filtering_by_date_created_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # Open preprints tab
#         wait_until_page_ready(driver)
#         # wait.until(EC.element_to_be_clickable(search_page_short.preprints_tab_link_xpath)).click()
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_date_created(driver, 'Date created')
#
#     def test_filtering_by_subject_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_subject(driver)
#
#     def test_filtering_by_license_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_license(driver)
#
#     # @pytest.mark.skip(reason='ENG-10674')
#     def test_filtering_by_institution_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_institution(driver)
#
#     def test_filtering_by_provider_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_provider(driver)
#
#     def test_filtering_by_supplemental_materials_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_supplemental_materials(driver)
#
#     def test_filtering_by_data_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#         public_data_xpath = "//section[.//h3[normalize-space()='Public Data']]//p[contains(text(),'http')]"
#         search_page_short.check_filtering_by_data(driver, public_data_xpath)
#
#     def test_filtering_by_preregistered_analysis_plan_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         base_page = BasePage(driver)
#         wait = WebDriverWait(driver, 25)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Additional Filters menu
#         additional_filters_menu = wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.additional_filters_menu_locator
#             )
#         )
#         additional_filters_menu.click()
#
#         # Select 'preregistered_analysis_plan' option
#         preregistered_analysis_plan_option_locator = (
#             By.XPATH,
#             "//input[@id='checkbox-hasPreregisteredAnalysisPlan']",
#         )
#         preregistered_analysis_plan_option = wait.until(
#             EC.presence_of_element_located(preregistered_analysis_plan_option_locator)
#         )
#         base_page.scroll_to(preregistered_analysis_plan_option)
#
#         # Save number of records related to the selected option 'preregistered_analysis_plan'
#         number_of_records = search_page_short.get_record_count_for_additional_filters(
#             driver, 'Preregistered analysis plan'
#         )
#
#         # Select 'preregistered_analysis_plan' option from the list
#         wait.until(
#             EC.presence_of_element_located(preregistered_analysis_plan_option_locator)
#         ).click()
#         wait_until_page_ready(driver)
#
#         # CHeck if results displays correct number of results.
#         result_count_after_filter_applying = search_page_short.get_results_count(driver)
#         assert result_count_after_filter_applying <= number_of_records
#
#         # Expand addition menu of the firs card
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.chevron_menu_first_card_locator
#             )
#         ).click()
#         wait_until_page_ready(driver)
#
#         #
#         element_on_card = (
#             By.XPATH,
#             "//p[contains(.,'Associated preregistration')]//a[contains(@href,'http')]",
#         )
#
#         assert wait.until(
#             EC.visibility_of_element_located(element_on_card)
#         ).is_displayed()
#
#     def test_filtering_by_preregistered_study_design_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         base_page = BasePage(driver)
#         wait = WebDriverWait(driver, 25)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Additional Filters menu
#         additional_filters_menu = wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.additional_filters_menu_locator
#             )
#         )
#         additional_filters_menu.click()
#
#         # Select 'preregistered_study_design' option
#         preregistered_study_design_option_locator = (
#             By.XPATH,
#             "//input[@id='checkbox-hasPreregisteredStudyDesign']",
#         )
#         preregistered_study_design_option = wait.until(
#             EC.presence_of_element_located(preregistered_study_design_option_locator)
#         )
#         base_page.scroll_to(preregistered_study_design_option)
#
#         # Save number of records related to the selected option 'preregistered_study_design'
#         number_of_records = search_page_short.get_record_count_for_additional_filters(
#             driver, 'Preregistered study design'
#         )
#
#         # Select 'preregistered_study_design' option from the list
#         wait.until(
#             EC.presence_of_element_located(preregistered_study_design_option_locator)
#         ).click()
#         wait_until_page_ready(driver)
#
#         # CHeck if results displays correct number of results.
#         result_count_after_filter_applying = search_page_short.get_results_count(driver)
#         assert result_count_after_filter_applying <= number_of_records
#
#         # Expand addition menu of the firs card
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.chevron_menu_first_card_locator
#             )
#         ).click()
#         wait_until_page_ready(driver)
#
#         #
#         element_on_card = (
#             By.XPATH,
#             "//p[contains(.,'Associated study design')]//a[contains(@href,'http')]",
#         )
#
#         assert wait.until(
#             EC.visibility_of_element_located(element_on_card)
#         ).is_displayed()
#
#     def test_clearing_of_applied_filters_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_clearing_of_applied_filters(driver)
#
#     def test_search_card_preprints(self, driver, institution_page, search_page_short):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#         _validate_preprint_card(driver, PreprintSearchResults(driver))
#
#     def test_sorting_by_created_date_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_sorting_by_created_date(driver, 'created')
#
#     def test_sorting_by_modified_date_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_sorting_by_modified_date(driver)
#
#     def test_search_in_filtering_by_creator_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Creator menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.creator_dropdown_menu_selector
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.additional_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_date_created_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Date Created menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.date_created_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.date_created_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_subject_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Subject menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.subject_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.subject_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_license_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand License menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.license_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.license_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_institution_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Institution menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.institution_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.institution_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_provider_on_preprints_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open preprints tab
#         search_page_short.preprints_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Provider menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.provider_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.provider_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#
# class TestInstitutionsPageRegistrationsTab:
#     def test_filtering_by_creator_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_creator(driver)
#
#     def test_filtering_by_date_created_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_date_created(driver, 'Date registered')
#
#     def test_filtering_by_subject_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_subject(driver)
#
#     def test_filtering_by_license_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_license(driver)
#
#     def test_filtering_by_institution_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_institution(driver)
#
#     def test_filtering_by_provider_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_provider(driver)
#
#     # @pytest.mark.skip(reason='ENG-10674')
#     def test_filtering_by_funder_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_funder(driver)
#
#     def test_filtering_by_resource_type_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_resource_type(driver, '', 'Registration')
#
#     def test_filtering_by_data_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#         data_xpath = "//i[contains(@class,'custom-icon-data')]"
#
#         search_page_short.check_filtering_by_data(driver, data_xpath)
#
#     def test_filtering_by_registration_template_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 25)
#         base_page = BasePage(driver)
#
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand "registration_template" menu
#         registration_template_menu = wait.until(
#             EC.presence_of_element_located(
#                 search_page_short.registration_template_menu_locator
#             )
#         )
#         base_page.scroll_to(registration_template_menu)
#
#         registration_template_menu.click()
#
#         # Click 'Select registration_template' drop-down menu
#         registration_template_multiselect_dropdown = wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.registration_template_multiselect_dropdown_selector
#             )
#         )
#         registration_template_multiselect_dropdown.click()
#
#         # Save name of the selected option (Template)
#         name_of_record = search_page_short.get_record_name(driver, '1')
#
#         # Save number of records related to the selected Template
#         number_of_records = search_page_short.get_record_count(driver, '1')
#
#         # Select First option from the list
#         wait_until_page_ready(driver)
#         template_first_option_locator = (
#             By.XPATH,
#             '(//ul[@role="listbox"]//li[@role="option"]//input[@type="checkbox"])[1]',
#         )
#
#         wait.until(
#             EC.presence_of_element_located(template_first_option_locator)
#         ).click()
#         wait_until_page_ready(driver)
#
#         # CHeck if results displays correct number of results.
#         result_count_after_filter_applying = search_page_short.get_results_count(driver)
#         assert result_count_after_filter_applying <= number_of_records
#
#         # Expand addition menu of the firs card
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.chevron_menu_first_card_locator
#             )
#         ).click()
#
#         # Check if cards in filtering results contains correct 'Template'.
#         record_locator = (
#             By.XPATH,
#             "//p[contains(normalize-space(),'Registration Template')]",
#         )
#
#         element = wait.until(EC.presence_of_element_located(record_locator))
#         base_page.scroll_to(element)
#
#         assert name_of_record in element.text
#
#     def test_filtering_by_includes_community_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_includes_community_schema(driver)
#
#     def test_filtering_by_analytic_code_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         selected_option_checkbox = 'hasAnalyticCodeResource'
#         additional_option_name = 'Analytic code'
#         icon_xpath = "//i[contains(@class,'custom-icon-code')]"
#
#         search_page_short.check_filtering_by_additional_options(
#             driver, selected_option_checkbox, additional_option_name, icon_xpath
#         )
#
#     def test_filtering_by_papers_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         selected_option_checkbox = 'hasPapersResource'
#         additional_option_name = 'Papers'
#         icon_xpath = "//i[contains(@class,'custom-icon-papers')]"
#
#         search_page_short.check_filtering_by_additional_options(
#             driver, selected_option_checkbox, additional_option_name, icon_xpath
#         )
#
#     def test_filtering_by_supplemental_resource_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         selected_option_checkbox = 'hasSupplementalResource'
#         additional_option_name = 'Supplemental resource'
#         icon_xpath = "//i[contains(@class,'custom-icon-supplements')]"
#
#         search_page_short.check_filtering_by_additional_options(
#             driver, selected_option_checkbox, additional_option_name, icon_xpath
#         )
#
#     def test_filtering_by_materials_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#
#         selected_option_checkbox = 'hasMaterialsResource'
#         additional_option_name = 'Materials'
#         icon_xpath = "//i[contains(@class,'custom-icon-supplements')]"
#
#         search_page_short.check_filtering_by_additional_options(
#             driver, selected_option_checkbox, additional_option_name, icon_xpath
#         )
#
#     def test_clearing_of_applied_filters_on_registration_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_clearing_of_applied_filters(driver)
#
#     def test_search_card_registrations(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#         _validate_registration_card(driver, RegistrationSearchResults(driver))
#
#     def test_sorting_by_created_date_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_sorting_by_created_date(driver, 'registered')
#
#     def test_sorting_by_modified_date_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_sorting_by_modified_date(driver)
#
#     def test_search_in_filtering_by_creator_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Creator menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.creator_dropdown_menu_selector
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.additional_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_date_created_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Date Created menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.date_created_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.date_created_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_funder_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Funder menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.funder_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.funder_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_subject_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Subject menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.subject_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.subject_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_license_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand License menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.license_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.license_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_resource_type_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Resource Type menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.resource_type_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.resource_type_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_institution_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Institution menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.institution_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.institution_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_community_schema_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Part of Community schema menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.includes_community_schema_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.includes_community_schema_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_provider_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Provider menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.provider_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.provider_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_registration_template_on_registrations_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.registrations_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand registration template menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.registration_template_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.registration_template_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#
# class TestInstitutionsPageFilesTab:
#     def test_filtering_by_date_created_on_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open files tab
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_date_created(driver, 'Date created')
#
#     def test_filtering_by_funder_on_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open files tab
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_funder(driver)
#
#     def test_filtering_by_license_on_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#
#         wait_until_page_ready(driver)
#         # Open files tab
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_license(driver)
#
#     def test_filtering_by_resource_type_on_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open files tab
#         base_page = BasePage(driver)
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#
#         wait = WebDriverWait(driver, 15)
#
#         # 1. Expand Resource Type menu
#         resource_type_menu = wait.until(
#             EC.presence_of_element_located(search_page_short.resource_type_menu_locator)
#         )
#         base_page.scroll_to(resource_type_menu)
#
#         resource_type_menu.click()
#
#         # Click 'Select Resource Type' drop-down menu
#         resource_type_multiselect_dropdown = wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.resource_type_multiselect_dropdown_selector
#             )
#         )
#         resource_type_multiselect_dropdown.click()
#         wait_until_page_ready(driver)
#
#         input_filed_locator = (
#             By.XPATH,
#             "//input[@role='searchbox' and contains(@class,'p-multiselect-filter')]",
#         )
#
#         wait.until(EC.visibility_of_element_located(input_filed_locator)).send_keys(
#             'Book'
#         )
#         wait_until_page_ready(driver)
#
#         # Save number of records related to the selected Resource Type
#         number_of_records = search_page_short.get_record_count(driver, '1')
#
#         # Select First option from the list
#         wait_until_page_ready(driver)
#         resource_type_first_option_locator = (
#             By.XPATH,
#             '(//ul[@role="listbox"]//li[@role="option"]//input[@type="checkbox"])[1]',
#         )
#
#         wait.until(
#             EC.presence_of_element_located(resource_type_first_option_locator)
#         ).click()
#
#         wait_until_page_ready(driver)
#
#         # CHeck if results displays correct number of results.
#         result_count_after_filter_applying = search_page_short.get_results_count(driver)
#         assert result_count_after_filter_applying <= number_of_records
#
#         # Expand addition menu of the firs card
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.chevron_menu_first_card_locator
#             )
#         ).click()
#         wait_until_page_ready(driver)
#         # Check if cards in filtering results contains correct 'Resource Type'.
#
#         resource_type_in_card_locator = (
#             By.XPATH,
#             "(//p[contains(normalize-space(),'Resource type:')])[1]",
#         )
#
#         element = wait.until(
#             EC.visibility_of_element_located(resource_type_in_card_locator)
#         )
#
#         assert 'Book' in element.text
#
#     def test_filtering_by_includes_community_on_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open registrations tab
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_includes_community_schema(driver)
#
#     def test_clearing_of_applied_filters_on_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open files tab
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_clearing_of_applied_filters(driver)
#
#     def test_sorting_by_created_date_on_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Switch to the Files Tab
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_sorting_by_created_date(driver, 'created')
#
#     def test_sorting_by_modified_date_on_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Switch to the Files Tab
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_sorting_by_modified_date(driver)
#
#     def test_search_card_files(self, driver, institution_page, search_page_short):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#         _validate_file_card(driver, FileSearchResults(driver))
#
#     def test_search_in_filtering_by_date_created_on_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Switch to the Files Tab
#         search_page_short.files_tab_link.click()
#
#         # 1. Expand Date Created menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.date_created_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.date_created_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_funder_on_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Switch to the Files Tab
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Funder menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.funder_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.funder_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_license_on_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # Switch to the Files Tab
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand License menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.license_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.license_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_community_schema_on_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Switch to the Files Tab
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Part of Community schema menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.includes_community_schema_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.includes_community_schema_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_resource_type_on_files_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         wait = WebDriverWait(driver, 15)
#         # Switch to the Files Tab
#         search_page_short.files_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Resource Type menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.resource_type_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.resource_type_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#
# class TestInstitutionsPageProjectsTab:
#
#     # @pytest.mark.skip(reason='ENG-10674')
#     def test_filtering_by_creator_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_creator(driver)
#
#     def test_filtering_by_date_created_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_date_created(driver, 'Date created')
#
#     # @pytest.mark.skip(reason='ENG-10674')
#     def test_filtering_by_funder_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_funder(driver)
#
#     # @pytest.mark.skip(reason='ENG-10674')
#     def test_filtering_by_subject_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_subject(driver)
#
#     def test_filtering_by_license_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_license(driver)
#
#     def test_filtering_by_institution_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_institution(driver)
#
#     # @pytest.mark.skip(reason='ENG-10674')
#     def test_filtering_by_part_of_collection_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_part_of_collection(driver)
#
#     # @pytest.mark.skip(reason='ENG-10674')
#     def test_filtering_by_includes_community_schema_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_filtering_by_includes_community_schema(driver)
#
#     def test_filtering_by_associated_preprint_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         wait = WebDriverWait(driver, 25)
#         base_page = BasePage(driver)
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Additional Filters menu
#         additional_filters_menu = wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.additional_filters_menu_locator
#             )
#         )
#         additional_filters_menu.click()
#
#         # Select additional option from the list
#         additional_option_locator = (By.XPATH, "//input[@id='checkbox-supplements']")
#
#         # skip tests if testing data is missing
#         try:
#             wait.until(EC.presence_of_element_located(additional_option_locator))
#         except TimeoutException:
#             pytest.skip('Record was not found in the list')
#
#         additional_option = wait.until(
#             EC.presence_of_element_located(additional_option_locator)
#         )
#         base_page.scroll_to(additional_option)
#
#         # Save number of records related to the selected additional option
#         number_of_records = search_page_short.get_record_count_for_additional_filters(
#             driver, 'Associated preprint'
#         )
#
#         # Select additional option from the list
#         wait.until(EC.presence_of_element_located(additional_option_locator)).click()
#         wait_until_page_ready(driver)
#
#         # CHeck if results displays correct number of results.
#         result_count_after_filter_applying = search_page_short.get_results_count(driver)
#         assert result_count_after_filter_applying <= number_of_records
#
#         # Click on the title os the first element in search results
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.first_search_result_title_locator
#             )
#         ).click()
#
#         # Switch to the second tab
#         wait.until(lambda d: len(d.window_handles) > 1)
#         driver.switch_to.window(driver.window_handles[-1])
#
#         # Check if page  contains selected option
#         wait_until_page_ready(driver)
#         locator = (By.XPATH, "//osf-overview-supplements//p[contains(., 'Preprints')]")
#
#         assert wait.until(EC.visibility_of_element_located(locator))
#
#     def test_clearing_of_applied_filters_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_clearing_of_applied_filters(driver)
#
#     # @pytest.mark.skip(reason='ENG-10674')
#     def test_filtering_by_resource_type_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Open projects tab
#         base_page = BasePage(driver)
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         wait = WebDriverWait(driver, 15)
#
#         # 1. Expand Resource Type menu
#         resource_type_menu = wait.until(
#             EC.presence_of_element_located(search_page_short.resource_type_menu_locator)
#         )
#         base_page.scroll_to(resource_type_menu)
#
#         resource_type_menu.click()
#
#         # Click 'Select Resource Type' drop-down menu
#         resource_type_multiselect_dropdown = wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.resource_type_multiselect_dropdown_selector
#             )
#         )
#         resource_type_multiselect_dropdown.click()
#         wait_until_page_ready(driver)
#
#         input_filed_locator = (
#             By.XPATH,
#             "//input[@role='searchbox' and contains(@class,'p-multiselect-filter')]",
#         )
#
#         wait.until(EC.visibility_of_element_located(input_filed_locator)).send_keys(
#             'Book'
#         )
#         wait_until_page_ready(driver)
#
#         # Save number of records related to the selected Resource Type
#         number_of_records = search_page_short.get_record_count(driver, '1')
#
#         # Select First option from the list
#         wait_until_page_ready(driver)
#         resource_type_first_option_locator = (
#             By.XPATH,
#             '(//ul[@role="listbox"]//li[@role="option"]//input[@type="checkbox"])[1]',
#         )
#
#         wait.until(
#             EC.presence_of_element_located(resource_type_first_option_locator)
#         ).click()
#
#         wait_until_page_ready(driver)
#
#         # CHeck if results displays correct number of results.
#         result_count_after_filter_applying = search_page_short.get_results_count(driver)
#         assert result_count_after_filter_applying == number_of_records
#
#         # Expand addition menu of the firs card
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.chevron_menu_first_card_locator
#             )
#         ).click()
#         wait_until_page_ready(driver)
#         # Check if cards in filtering results contains correct 'Resource Type'.
#
#         resource_type_in_card_locator = (
#             By.XPATH,
#             "(//p[contains(normalize-space(),'Resource type:')])[1]",
#         )
#
#         element = wait.until(
#             EC.visibility_of_element_located(resource_type_in_card_locator)
#         )
#
#         assert 'Book' in element.text
#
#     def test_sorting_by_created_date_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # search_page_short.loading_indicator.here_then_gone()
#         # Switch to the Projects Tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_sorting_by_created_date(driver, 'created')
#
#     def test_sorting_by_modified_date_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # search_page.loading_indicator.here_then_gone()
#         # Switch to the Projects Tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_sorting_by_modified_date(driver)
#
#     def test_search_in_filtering_by_creator_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Creator menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.creator_dropdown_menu_selector
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.additional_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_date_created_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Date Created menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.date_created_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.date_created_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_funder_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Funder menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.funder_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.funder_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_subject_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Subject menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.subject_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.subject_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_license_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand License menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.license_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.license_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_resource_type_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Resource Type menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.resource_type_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.resource_type_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_institution_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Institution menu
#         wait.until(
#             EC.visibility_of_element_located(search_page_short.institution_menu_locator)
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.institution_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_part_of_collection_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Part of Collection menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.part_of_collection_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.part_of_collection_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_in_filtering_by_community_schema_on_projects_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         # Open projects tab
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#
#         # 1. Expand Part of Community schema menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.includes_community_schema_menu_locator
#             )
#         ).click()
#
#         # Click 'multiselect_dropdown' drop-down menu
#         wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.includes_community_schema_multiselect_dropdown_selector
#             )
#         ).click()
#
#         search_page_short.check_search_in_filtering_options(driver)
#
#     def test_search_card_projects(self, driver, institution_page, search_page_short):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         search_page_short.projects_tab_link.click()
#         wait_until_page_ready(driver)
#         _validate_project_card(driver, ProjectSearchResults(driver))
#
#
# class TestInstitutionsPageUsersTab:
#     def test_sorting_by_created_date_on_users_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         search_page_short.loading_indicator.here_then_gone()
#         # Switch to the Users Tab
#         search_page_short.users_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_sorting_by_created_date(driver, 'created')
#
#     def test_sorting_by_modified_date_on_users_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         search_page_short.loading_indicator.here_then_gone()
#         # Switch to the Users Tab
#         search_page_short.users_tab_link.click()
#         wait_until_page_ready(driver)
#
#         search_page_short.check_sorting_by_modified_date(driver)
#
#     def test_search_results_exist_users_tab(
#         self, driver, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         search_page_short.loading_indicator.here_then_gone()
#         # Switch to the Users Tab
#         search_page_short.users_tab_link.click()
#         search_page_short.loading_indicator.here_then_gone()
#         WebDriverWait(driver, 10).until(
#             EC.visibility_of_element_located(
#                 (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
#             )
#         )
#         assert len(search_page_short.search_results) > 0
#         # Verify that first search result is of User type
#         assert search_page_short.first_card_object_type_label.text == 'User'
#
#     def test_filtering_on_users_tab(self, driver, institution_page, search_page_short):
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         search_page_short.loading_indicator.here_then_gone()
#         # Switch to the Users Tab
#         search_page_short.users_tab_link.click()
#         wait_until_page_ready(driver)
#         wait.until(
#             EC.visibility_of_element_located(
#                 (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
#             )
#         )
#
#         # 1. Expand Institution menu
#         institution_menu = wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.institution_menu_selector
#             )
#         )
#         institution_menu.click()
#
#         # Click 'Select institution' drop-down menu
#         institution_multiselect_dropdown = wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.additional_multiselect_dropdown_selector
#             )
#         )
#         institution_multiselect_dropdown.click()
#
#         institution_first_option_locator = (
#             By.XPATH,
#             '(//ul[@role="listbox"]//li[@role="option"])[1]',
#         )
#         # Save name of the selected institution
#         name_of_institution = search_page_short.get_record_name(driver, '1')
#
#         # Save number of users related to the institution.
#         number_of_users = search_page_short.get_record_count(driver, '1')
#
#         # Select First institution from the list
#         wait.until(
#             EC.visibility_of_element_located(institution_first_option_locator)
#         ).click()
#         wait_until_page_ready(driver)
#
#         # CHeck if results displays correct number of users.
#         result_count_after_filter_applying = search_page_short.get_results_count(driver)
#         assert result_count_after_filter_applying == number_of_users
#
#         # Check if cards in filtering results contains name of institution.
#         institution_locator = (
#             By.XPATH,
#             f'//p-accordion-panel//a[contains(normalize-space(), "{name_of_institution}")]',
#         )
#
#         element = wait.until(EC.visibility_of_element_located(institution_locator))
#
#         assert element.is_displayed()
#
#     def test_clearing_of_applied_filters_on_users_tab(
#         self, driver, institution_page, search_page_short
#     ):
#
#         wait = WebDriverWait(driver, 15)
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         wait_until_page_ready(driver)
#         # Switch to the Users Tab
#         search_page_short.users_tab_link.click()
#         search_page_short.loading_indicator.here_then_gone()
#         wait.until(
#             EC.visibility_of_element_located(
#                 (By.CSS_SELECTOR, 'osf-resource-card .resource.p-4')
#             )
#         )
#         # save number of results without filters
#         result_count_without_filter = search_page_short.get_results_count(driver)
#
#         #
#         # 1. Expand Institution menu
#         institution_menu = wait.until(
#             EC.visibility_of_element_located(
#                 search_page_short.institution_menu_selector
#             )
#         )
#         institution_menu.click()
#
#         # Click 'Select institution' drop-down menu
#         institution_multiselect_dropdown = wait.until(
#             EC.visibility_of_element_located((By.ID, 'any-of'))
#         )
#         institution_multiselect_dropdown.click()
#
#         # Select First institution from the list
#         first_option_locator = (
#             By.XPATH,
#             '(//ul[@role="listbox"]//li[@role="option"])[2]',
#         )
#
#         wait.until(EC.element_to_be_clickable(first_option_locator)).click()
#
#         #
#         wait_until_page_ready(driver)
#
#         # Check that number of results is changes
#         result_count_after_filter_applying = search_page_short.get_results_count(driver)
#         assert result_count_after_filter_applying != result_count_without_filter
#
#         # Clear applied filter.
#         remove_button_locator = (By.CSS_SELECTOR, 'span.p-chip-remove-icon')
#
#         wait.until(EC.element_to_be_clickable(remove_button_locator)).click()
#
#         # Check that initial numbers of result is the same that displayed
#         wait_until_page_ready(driver)
#         result_count_after_removing_filter = search_page_short.get_results_count(driver)
#         assert result_count_without_filter == result_count_after_removing_filter
#
#     def test_search_card_users(
#         self, driver, user_search_page, institution_page, search_page_short
#     ):
#         wait_until_page_ready(driver)
#         select_institution(driver, institution_page, 'Center For Open Science')
#         search_page_short.loading_indicator.here_then_gone()
#         # Switch to the Users Tab
#         search_page_short.users_tab_link.click()
#         wait_until_page_ready(driver)
#
#         WebDriverWait(driver, 10).until(
#             EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
#         )
#         assert len(user_search_page.search_results) > 0
#
#         # Collect user information from the search card
#         search_card_name = user_search_page.user_name.text.strip()
#         has_orcid = user_search_page.orcid_badge.present()
#
#         # Expand the accordion to reveal secondary metadata
#         user_search_page.secondary_metadata_dropdown.click()
#         WebDriverWait(driver, 10).until(
#             EC.text_to_be_present_in_element(
#                 (
#                     By.CSS_SELECTOR,
#                     'osf-resource-card:first-of-type osf-user-secondary-metadata',
#                 ),
#                 'Public projects',
#             )
#         )
#
#         # Collect secondary metadata counts from the first search card
#         public_projects = int(
#             user_search_page.user_public_projects.text.split(':')[1].strip()
#         )
#         public_registrations = int(
#             user_search_page.user_public_registrations.text.split(':')[1].strip()
#         )
#         public_preprints = int(
#             user_search_page.user_public_preprints.text.split(':')[1].strip()
#         )
#
#         # Click user name link to navigate to profile page
#         user_search_page.user_name.click_expecting_popup()
#         WebDriverWait(driver, 15).until(
#             EC.visibility_of_element_located(
#                 (By.CSS_SELECTOR, 'osf-profile-information')
#             )
#         )
#
#         # Verify the profile page name matches the search card name
#         profile_page = UserProfilePage(driver)
#         profile_name = profile_page.profile_name.text.strip()
#         assert search_card_name == profile_name
#         if has_orcid:
#             assert profile_page.orcid_link.present()
#
#         WebDriverWait(driver, 15).until(
#             EC.invisibility_of_element_located((By.CSS_SELECTOR, 'p-progress-spinner'))
#         )
#
#         # Verify Projects count
#         if public_projects > 0:
#             profile_page.projects_tab.click()
#             WebDriverWait(driver, 10).until(
#                 EC.invisibility_of_element_located(
#                     (By.CSS_SELECTOR, 'p-progress-spinner')
#                 )
#             )
#             WebDriverWait(driver, 15).until(
#                 EC.text_to_be_present_in_element(
#                     (By.CSS_SELECTOR, 'p.type.py-1.px-3.font-bold'), 'Project'
#                 )
#             )
#             result_text = profile_page.result_count.text.strip()
#             profile_projects = int(result_text.split()[0])
#             # note: projects marked as 'spam' are not counted on the user profile page
#             assert public_projects >= profile_projects
#
#         # Verify Registrations count
#         if public_registrations > 0:
#             profile_page.registrations_tab.click()
#             WebDriverWait(driver, 10).until(
#                 EC.invisibility_of_element_located(
#                     (By.CSS_SELECTOR, 'p-progress-spinner')
#                 )
#             )
#             WebDriverWait(driver, 15).until(
#                 EC.text_to_be_present_in_element(
#                     (By.CSS_SELECTOR, 'p.type.py-1.px-3.font-bold'),
#                     'Registration',
#                 )
#             )
#             result_text = profile_page.result_count.text.strip()
#             profile_registrations = int(result_text.split()[0])
#             # note: withdrawn registrations are not counted on the user profile page
#             assert public_registrations >= profile_registrations
#
#         # Verify Preprints count
#         if public_preprints > 0:
#             profile_page.preprints_tab.click()
#             WebDriverWait(driver, 10).until(
#                 EC.invisibility_of_element_located(
#                     (By.CSS_SELECTOR, 'p-progress-spinner')
#                 )
#             )
#             WebDriverWait(driver, 15).until(
#                 EC.text_to_be_present_in_element(
#                     (By.CSS_SELECTOR, 'p.type.py-1.px-3.font-bold'), 'Preprint'
#                 )
#             )
#             result_text = profile_page.result_count.text.strip()
#             profile_preprints = int(result_text.split()[0])
#             # note: withdrawn preprints are not counted on the user profile page
#             assert public_preprints >= profile_preprints


@markers.two_minute_drill
@markers.core_functionality
class TestInstitutionLandingPages:
    """This test will load the landing page for each Institution that exists in
    an environment.
    """

    def institutions():
        """Return institutions to be used in Discover page test. The list of
        institutions in some environments (i.e. Staging2) has gotten very long."""
        all_inst = osf_api.get_all_institutions_data()
        return [institution['id'] for institution in all_inst]

    @pytest.mark.parametrize('institution', institutions())
    def test_institution_landing_page(self, session, driver, institution):
        discover_page = InstitutionBrandedPage(driver, institution_id=institution)
        discover_page.goto_short()
        assert InstitutionBrandedPage(driver, verify=True)
