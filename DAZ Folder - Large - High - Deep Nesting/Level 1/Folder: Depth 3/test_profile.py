import re
from datetime import datetime

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import markers
import utils
from api import osf_api
from pages.base import BasePage
from pages.file_detail import FileDetailPage
from pages.preprints import PreprintDetailPage
from pages.profile import ProfilePage
from pages.project import ProjectPage
from pages.registries import RegistrationDetailPage
from pages.search import (
    FileSearchResults,
    PreprintSearchResults,
    ProjectSearchResults,
    RegistrationSearchResults,
    SearchPage,
    SearchPageHelpers,
)
from utils import (
    normalize_ui_date,
    wait_until_page_ready,
)


@pytest.fixture()
def profile_page_short(driver):
    profile_page = ProfilePage(driver)
    profile_page.goto_short()
    return profile_page


@pytest.fixture()
def search_page_helpers(driver):
    search_page_helpers = SearchPageHelpers(driver)
    return search_page_helpers


def open_projects_tab(driver, search_page_helpers):
    wait = WebDriverWait(driver, 20)
    wait.until(
        EC.element_to_be_clickable(search_page_helpers.projects_tab_link_locator)
    ).click()
    wait_until_page_ready(driver)


def open_preprints_tab(driver, search_page_helpers):
    wait = WebDriverWait(driver, 20)
    wait.until(
        EC.element_to_be_clickable(search_page_helpers.preprints_tab_link_xpath)
    ).click()
    wait_until_page_ready(driver)


def open_registrations_tab(driver, search_page_helpers):
    wait = WebDriverWait(driver, 20)
    wait.until(
        EC.element_to_be_clickable(search_page_helpers.registrations_tab_link_locator)
    ).click()
    wait_until_page_ready(driver)


def open_files_tab(driver, search_page_helpers):
    wait = WebDriverWait(driver, 20)
    wait.until(
        EC.element_to_be_clickable(search_page_helpers.files_tab_link_locator)
    ).click()
    wait_until_page_ready(driver)


# @pytest.mark.usefixtures('must_be_logged_in')
@markers.dont_run_on_prod
class TestProfilePageProjectsTab:

    # @pytest.mark.skip(reason='ENG-10674')
    def test_filtering_by_creator_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)

        # Open projects
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)

        search_page_helpers.check_filtering_by_creator(driver, '1')

    def test_filtering_by_date_created_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_date_created(driver, 'Date created')

    def test_filtering_by_institution_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_institution(driver, '1')

    def test_filtering_by_subject_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_subject(driver, '1')

    def test_filtering_by_license_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_license(driver)

    def test_filtering_by_funder_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_funder(driver)

    @pytest.mark.skip(reason='ENG-10778')
    def test_filtering_by_part_of_collection_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_part_of_collection(driver)

    # @pytest.mark.skip(reason='ENG-10778')
    def test_filtering_by_community_schema_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_includes_community_schema(driver)

    @pytest.mark.skip(reason='ENG-10778')
    def test_filtering_by_additional_option_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_additional_options(driver, '', '', '')

    def test_filtering_by_resource_type_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_resource_type(driver, '', 'Book')

    def test_clearing_of_applied_filters_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_clearing_of_applied_filters(driver)

    def test_sorting_by_created_date_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # search_page_short.loading_indicator.here_then_gone()
        # Switch to the Projects Tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_sorting_by_created_date(driver, 'created')

    def test_sorting_by_modified_date_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # search_page.loading_indicator.here_then_gone()
        # Switch to the Projects Tab
        open_projects_tab(driver, search_page_helpers)

        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_sorting_by_modified_date(driver)

    def test_search_in_filtering_by_creator_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand Creator menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.creator_dropdown_menu_selector
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.additional_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_date_created_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand Date Created menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.date_created_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.date_created_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_institution_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand Institution menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.institution_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.institution_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    # @pytest.mark.skip(reason='ENG-10778')
    def test_search_in_filtering_by_funder_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)

        # 1. Expand Funder menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.funder_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.funder_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_subject_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand Subject menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.subject_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.subject_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_license_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand License menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.license_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.license_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_resource_type_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open projects tab
        open_projects_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand Resource Type menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.resource_type_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.resource_type_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    @pytest.mark.skip(reason='ENG-10778')
    def test_search_in_filtering_by_part_of_collection_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)

        # 1. Expand Part of Collection menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.part_of_collection_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.part_of_collection_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_card_projects(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.projects_tab_link.click()
        wait_until_page_ready(driver)
        _validate_project_card(driver, ProjectSearchResults(driver))


class TestProfilePageAllTab:
    # @pytest.mark.skip(reason='ENG-10674')
    def test_filtering_by_creator_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)

        search_page_helpers.check_filtering_by_creator(driver, '1')

    def test_filtering_by_date_created_on_projects_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_date_created(driver, 'Date')

    def test_filtering_by_institution_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_institution(driver, '1')

    def test_filtering_by_subject_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_subject(driver, '1')

    def test_filtering_by_license_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_license(driver)

    # @pytest.mark.skip(reason='ENG-10778')
    def test_filtering_by_funder_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_funder(driver)

    def test_filtering_by_provider_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_provider(driver, '2')

    @pytest.mark.skip(reason='ENG-10778')
    def test_filtering_by_additional_option_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_additional_options(driver, '', '', '')

    @pytest.mark.skip(reason='ENG-10778')
    def test_filtering_by_part_of_collection_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_part_of_collection(driver)

    def test_filtering_by_resource_type_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_resource_type(driver, '', 'Registration')

    def test_clearing_of_applied_filters_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_clearing_of_applied_filters(driver)

    def test_sorting_by_created_date_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):

        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_sorting_by_created_date(driver, 'created')

    def test_sorting_by_modified_date_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):

        wait_until_page_ready(driver)

        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_sorting_by_modified_date(driver)

    def test_search_in_filtering_by_creator_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand Creator menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.creator_dropdown_menu_selector
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.additional_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_date_created_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand Date Created menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.date_created_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.date_created_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_institution_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand Institution menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.institution_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.institution_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    # @pytest.mark.skip(reason='ENG-10778')
    def test_search_in_filtering_by_funder_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)

        # 1. Expand Funder menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.funder_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.funder_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_subject_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand Subject menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.subject_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.subject_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_license_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand License menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.license_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.license_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_resource_type_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand Resource Type menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.resource_type_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.resource_type_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_provider_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand Provider menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.provider_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.provider_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver, '2')

    @pytest.mark.skip(reason='ENG-10778')
    def test_search_in_filtering_by_part_of_collection_on_all_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)

        # 1. Expand Part of Collection menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.part_of_collection_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.part_of_collection_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_card_all(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        WebDriverWait(driver, 25).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
        )

        search_page = SearchPage(driver)
        assert len(search_page.search_results) > 0

        result_type = search_page.node_type.text.strip()

        dispatch = {
            'Project': lambda: _validate_project_card(
                driver, ProjectSearchResults(driver)
            ),
            'Registration': lambda: _validate_registration_card(
                driver, RegistrationSearchResults(driver)
            ),
            'Preprint': lambda: _validate_preprint_card(
                driver, PreprintSearchResults(driver)
            ),
            'File': lambda: _validate_file_card(driver, FileSearchResults(driver)),
        }

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


def _validate_preprint_card(driver, preprint_page):
    WebDriverWait(driver, 25).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
    )
    assert len(preprint_page.search_results) > 0

    preprint_title = preprint_page.preprint_title.text
    search_date_text_full = preprint_page.date_created.text
    search_card_date = search_date_text_full.split('Date created:')[1].strip()

    card_contributor_elements = preprint_page.preprint_card_contributor_links
    card_contributor_names = [
        el.text.strip().rstrip(',').strip() for el in card_contributor_elements
    ]
    has_more_contributors = preprint_page.preprint_card_contributors_more.present()
    more_count = 0
    if has_more_contributors:
        more_text = preprint_page.preprint_card_contributors_more.text
        match = re.search(r'\d+', more_text)
        more_count = int(match.group()) if match else 0

    preprint_page.preprint_title.click_expecting_popup()
    WebDriverWait(driver, 25).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-preprint-details'))
    )
    wait_until_page_ready(driver)

    preprint_detail = PreprintDetailPage(driver)
    preprint_detail_title = preprint_detail.preprint_title.element.text

    has_date_on_detail = preprint_detail.date_created.present()
    if has_date_on_detail:
        preprint_date_text_full = preprint_detail.date_created.text
        preprint_date_created = preprint_date_text_full.split('Submitted:')[1].strip()

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-test-contributor-name]')
            )
        )
    except TimeoutException:
        pass

    detail_contributor_names = [
        el.text.strip().rstrip(',').strip() for el in preprint_detail.all_contributors
    ]

    assert preprint_title == preprint_detail_title
    if has_date_on_detail:
        assert (
            normalize_ui_date(search_card_date)[:10]
            == normalize_ui_date(preprint_date_created)[:10]
        )

    try:
        total_on_detail = len(detail_contributor_names)
        if total_on_detail == 0:
            assert len(card_contributor_names) == 0
            assert not has_more_contributors
        elif total_on_detail <= 4:
            assert sorted(card_contributor_names) == sorted(detail_contributor_names)
            assert not has_more_contributors
        else:
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


def _validate_registration_card(driver, registration_page):
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
    )
    assert len(registration_page.search_results) > 0

    withdrawn_badge = driver.find_elements(
        By.XPATH,
        '(//osf-resource-card)[1]//p-tag[contains(normalize-space(.), "Withdrawn")]',
    )
    if withdrawn_badge:
        pytest.skip('Withdrawn Registration')

    card_contributor_elements = registration_page.registration_card_contributor_links
    card_contributor_names = [
        el.text.strip().rstrip(',').strip() for el in card_contributor_elements
    ]
    has_more_contributors = (
        registration_page.registration_card_contributors_more.present()
    )
    more_count = 0
    if has_more_contributors:
        more_text = registration_page.registration_card_contributors_more.text
        match = re.search(r'\d+', more_text)
        more_count = int(match.group()) if match else 0

    search_card_title = registration_page.registration_title.text
    dates = registration_page.registration_dates.text.split('|')
    search_card_reg_date = dates[0].replace('Date registered:', '').strip()

    registration_page.secondary_metadata_dropdown.click()
    WebDriverWait(driver, 20).until(
        EC.text_to_be_present_in_element(
            (
                By.CSS_SELECTOR,
                'osf-resource-card:first-of-type osf-registration-secondary-metadata',
            ),
            'URL',
        )
    )

    search_card_provider = registration_page.registration_provider.text.split(
        'Provider:'
    )[1].strip()
    search_card_template = registration_page.registration_template.text.split(
        'Registration Template:'
    )[1].strip()
    search_card_url = registration_page.registration_url.text.split('URL:')[1].strip()

    has_license_on_card = registration_page.registration_license.present()
    if has_license_on_card:
        search_card_license = registration_page.registration_license.text.split(
            'License:'
        )[1].strip()

    has_doi_on_card = registration_page.registration_doi.present()
    if has_doi_on_card:
        search_card_doi = registration_page.registration_doi.text.split('DOI:')[
            1
        ].strip()

    registration_page.registration_title.click_expecting_popup()
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'osf-registration-blocks-data')
        )
    )
    wait_until_page_ready(driver)

    WebDriverWait(driver, 15).until(
        lambda d: d.find_element(
            By.XPATH, '//h3[normalize-space()="Registry"]/following-sibling::p'
        ).text.strip()
        != ''
    )

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-test-contributor-name]')
            )
        )
    except TimeoutException:
        pass

    reg_detail = RegistrationDetailPage(driver)
    reg_title = reg_detail.title.element.text
    registered_date = reg_detail.registered_date.text

    detail_contributor_names = [
        el.text.strip().rstrip(',').strip() for el in reg_detail.all_contributors
    ]

    assert search_card_title == reg_title
    assert (
        normalize_ui_date(search_card_reg_date)[:10]
        == normalize_ui_date(registered_date)[:10]
    )
    assert search_card_provider == reg_detail.overview_registry.text
    assert search_card_template == reg_detail.overview_registration_type.text
    assert search_card_url in driver.current_url
    if has_license_on_card:
        assert search_card_license == reg_detail.overview_license.text
    if has_doi_on_card:
        detail_doi = reg_detail.registration_doi.text
        assert detail_doi in search_card_doi

    try:
        total_on_detail = len(detail_contributor_names)
        if total_on_detail == 0:
            assert len(card_contributor_names) == 0
            assert not has_more_contributors
        elif total_on_detail <= 4:
            assert sorted(card_contributor_names) == sorted(detail_contributor_names)
            assert not has_more_contributors
        else:
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


def _validate_project_card(driver, project_page):
    WebDriverWait(driver, 25).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
    )
    assert len(project_page.search_results) > 0

    for _ in range(3):
        if project_page.first_card_type.text != 'Project Component':
            break
        driver.refresh()
        WebDriverWait(driver, 25).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
        )
    else:
        pytest.skip('Project component skipped')

    project_title = project_page.project_title.text
    dates = project_page.project_dates.text.split('|')
    search_card_date_created = dates[0].replace('Date created:', '').strip()

    project_page.secondary_metadata_dropdown.click()
    WebDriverWait(driver, 20).until(
        EC.text_to_be_present_in_element(
            (
                By.CSS_SELECTOR,
                'osf-resource-card:first-of-type osf-project-secondary-metadata',
            ),
            'URL',
        )
    )

    has_license_on_card = project_page.project_license.present()
    if has_license_on_card:
        search_card_license = project_page.project_license.text.split('License:')[
            1
        ].strip()

    has_doi_on_card = project_page.project_doi.present()
    if has_doi_on_card:
        search_card_doi = project_page.project_doi.text.split('DOI:')[1].strip()

    has_collection_on_card = project_page.project_collection.present()
    if has_collection_on_card:
        search_card_collection = project_page.project_collection.text.split(
            'Collection:'
        )[1].strip()

    project_page.project_title.click_expecting_popup()
    WebDriverWait(driver, 25).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'h1.flex.align-items-center')
        )
    )
    wait_until_page_ready(driver)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    '//h3[normalize-space()="Contributors"]/following-sibling::div//a',
                )
            )
        )
    except TimeoutException:
        pass

    project_detail = ProjectPage(driver)
    project_detail_title = project_detail.title.element.text
    project_detail_date_created = project_detail.date_created.text
    project_detail_license = project_detail.license.text

    print(f'\nProject URL: {driver.current_url}')

    assert project_title == project_detail_title
    assert (
        normalize_ui_date(search_card_date_created)[:10]
        == normalize_ui_date(project_detail_date_created)[:10]
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


def _validate_file_card(driver, file_page):
    search_page = SearchPage(driver)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'osf-resource-card'))
    )
    assert len(file_page.search_results) > 0

    search_card_title = file_page.file_title.text.strip()
    from_href = file_page.from_project_link.get_attribute('href')
    parent_project_guid = from_href.rstrip('/').split('/')[-1]

    wait = WebDriverWait(driver, 20)
    wait.until(
        EC.visibility_of_element_located(search_page.chevron_menu_first_card_locator)
    ).click()
    try:
        search_card_funder = file_page.funder_link.text.strip()
    except ValueError:
        search_card_funder = None

    file_page.file_title.click_expecting_popup()
    wait_until_page_ready(driver)

    if '/preprints/' in driver.current_url:
        pytest.skip(
            'File belongs to a preprint — navigates to preprint page, not file detail'
        )

    file_detail_page = FileDetailPage(driver)
    file_detail_title = file_detail_page.file_title.text.strip()
    assert search_card_title == file_detail_title

    breadcrumb_text = file_detail_page.breadcrumbs.text.lower()
    assert parent_project_guid in breadcrumb_text

    if search_card_funder:
        detail_funder = file_detail_page.funder.text.strip()
        assert search_card_funder == detail_funder


@markers.dont_run_on_prod
class TestProfilePageRegistrationsTab:
    def test_filtering_by_creator_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_creator(driver)

    def test_filtering_by_date_created_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_date_created(driver, 'Date registered')

    def test_filtering_by_subject_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_subject(driver, '1')

    def test_filtering_by_license_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_license(driver)

    def test_filtering_by_institution_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_institution(driver, '1')

    def test_filtering_by_provider_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_provider(driver)

    def test_filtering_by_funder_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_funder(driver)

    def test_filtering_by_resource_type_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_resource_type(driver, '', 'Registration')

    def test_filtering_by_data_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)
        data_xpath = "//i[contains(@class,'custom-icon-data')]"

        search_page_helpers.check_filtering_by_data(driver, data_xpath)

    def test_filtering_by_registration_template_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 25)
        base_page = BasePage(driver)

        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        # 1. Expand "registration_template" menu
        registration_template_menu = wait.until(
            EC.presence_of_element_located(
                search_page_helpers.registration_template_menu_locator
            )
        )
        base_page.scroll_to(registration_template_menu)

        registration_template_menu.click()

        # Click 'Select registration_template' drop-down menu
        registration_template_multiselect_dropdown = wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.registration_template_multiselect_dropdown_selector
            )
        )
        registration_template_multiselect_dropdown.click()

        # Save name of the selected option (Template)
        name_of_record = search_page_helpers.get_record_name(driver, '1')

        # Save number of records related to the selected Template
        number_of_records = search_page_helpers.get_record_count(driver, '1')

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
        result_count_after_filter_applying = search_page_helpers.get_results_count(
            driver
        )
        assert result_count_after_filter_applying <= number_of_records

        # Expand addition menu of the firs card
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.chevron_menu_first_card_locator
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
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_includes_community_schema(driver)

    def test_filtering_by_analytic_code_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        selected_option_checkbox = 'hasAnalyticCodeResource'
        additional_option_name = 'Analytic code'
        icon_xpath = "//i[contains(@class,'custom-icon-code')]"

        search_page_helpers.check_filtering_by_additional_options(
            driver, selected_option_checkbox, additional_option_name, icon_xpath
        )

    def test_filtering_by_papers_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        selected_option_checkbox = 'hasPapersResource'
        additional_option_name = 'Papers'
        icon_xpath = "//i[contains(@class,'custom-icon-papers')]"

        search_page_helpers.check_filtering_by_additional_options(
            driver, selected_option_checkbox, additional_option_name, icon_xpath
        )

    def test_filtering_by_supplemental_resource_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        selected_option_checkbox = 'hasSupplementalResource'
        additional_option_name = 'Supplemental resource'
        icon_xpath = "//i[contains(@class,'custom-icon-supplements')]"

        search_page_helpers.check_filtering_by_additional_options(
            driver, selected_option_checkbox, additional_option_name, icon_xpath
        )

    def test_filtering_by_materials_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        search_page_helpers.registrations_tab_link.click()

        selected_option_checkbox = 'hasMaterialsResource'
        additional_option_name = 'Materials'
        icon_xpath = "//i[contains(@class,'custom-icon-supplements')]"

        search_page_helpers.check_filtering_by_additional_options(
            driver, selected_option_checkbox, additional_option_name, icon_xpath
        )

    def test_clearing_of_applied_filters_on_registration_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        search_page_helpers.check_clearing_of_applied_filters(driver)

    def test_sorting_by_created_date_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        search_page_helpers.check_sorting_by_created_date(driver, 'registered')

    def test_sorting_by_modified_date_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        search_page_helpers.check_sorting_by_modified_date(driver)

    def test_search_in_filtering_by_creator_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        # 1. Expand Creator menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.creator_dropdown_menu_selector
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.additional_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_date_created_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        # 1. Expand Date Created menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.date_created_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.date_created_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_funder_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        # 1. Expand Funder menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.funder_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.funder_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_subject_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        # 1. Expand Subject menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.subject_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.subject_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_license_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        # 1. Expand License menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.license_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.license_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_resource_type_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        # 1. Expand Resource Type menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.resource_type_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.resource_type_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_institution_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        # 1. Expand Institution menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.institution_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.institution_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_community_schema_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        # 1. Expand Part of Community schema menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.includes_community_schema_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.includes_community_schema_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_provider_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        # 1. Expand Provider menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.provider_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.provider_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_registration_template_on_registrations_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 25)
        wait_until_page_ready(driver)
        # Open registrations tab
        open_registrations_tab(driver, search_page_helpers)

        # 1. Expand registration template menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.registration_template_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.registration_template_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_card_registrations(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.registrations_tab_link.click()
        wait_until_page_ready(driver)
        _validate_registration_card(driver, RegistrationSearchResults(driver))


@markers.dont_run_on_prod
class TestProfilePagePreprintsTab:
    def test_filtering_by_creator_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_creator(driver)

    def test_filtering_by_date_created_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_date_created(driver, 'Date created')

    def test_filtering_by_subject_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_subject(driver, '1')

    def test_filtering_by_license_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_license(driver)

    def test_filtering_by_institution_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_institution(driver, '1')

    def test_filtering_by_provider_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_provider(driver)

    def test_filtering_by_supplemental_materials_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        search_page_helpers.check_filtering_by_supplemental_materials(driver)

    def test_clearing_of_applied_filters_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        search_page_helpers.check_clearing_of_applied_filters(driver)

    def test_sorting_by_created_date_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        search_page_helpers.check_sorting_by_created_date(driver, 'registered')

    def test_sorting_by_modified_date_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        search_page_helpers.check_sorting_by_modified_date(driver)

    def test_search_in_filtering_by_creator_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        # 1. Expand Creator menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.creator_dropdown_menu_selector
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.additional_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_date_created_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        # 1. Expand Date Created menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.date_created_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.date_created_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_subject_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        # 1. Expand Subject menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.subject_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.subject_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_license_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        # 1. Expand License menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.license_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.license_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_institution_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        # 1. Expand Institution menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.institution_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.institution_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_provider_on_preprints_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 25)
        wait_until_page_ready(driver)
        # Open preprints tab
        open_preprints_tab(driver, search_page_helpers)

        # 1. Expand Provider menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.provider_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.provider_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_card_preprints(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.preprints_tab_link.click()
        wait_until_page_ready(driver)
        _validate_preprint_card(driver, PreprintSearchResults(driver))


@markers.dont_run_on_prod
class TestProfilePageFilesTab:
    def test_filtering_by_date_created_on_files_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open files tab
        open_files_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_date_created(driver, 'Date created')

    def test_filtering_by_funder_on_files_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open files tab
        open_files_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_funder(driver)

    def test_filtering_by_license_on_files_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open files tab
        open_files_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_license(driver)

    def test_filtering_by_resource_type_on_files_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open files tab
        open_files_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_resource_type(driver, '', 'Book')

    def test_filtering_by_community_schema_on_files_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open files tab
        open_files_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_filtering_by_includes_community_schema(driver)

    def test_clearing_of_applied_filters_on_files_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # Open files tab
        open_files_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_clearing_of_applied_filters(driver)

    def test_search_in_filtering_by_date_created_on_files_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        wait = WebDriverWait(driver, 15)
        # Open projects tab
        open_files_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand Date Created menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.date_created_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.date_created_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_funder_on_files_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open projects tab
        open_files_tab(driver, search_page_helpers)

        # 1. Expand Funder menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.funder_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.funder_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_license_on_files_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open files tab
        open_files_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand License menu
        wait.until(
            EC.visibility_of_element_located(search_page_helpers.license_menu_locator)
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.license_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_search_in_filtering_by_resource_type_on_files_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open files tab
        open_files_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)

        # 1. Expand Resource Type menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.resource_type_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.resource_type_multiselect_dropdown_selector
            )
        ).click()

    def test_search_in_filtering_by_community_schema_on_files_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait = WebDriverWait(driver, 15)
        wait_until_page_ready(driver)
        # Open files tab
        open_files_tab(driver, search_page_helpers)

        # 1. Expand Part of Community schema menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.includes_community_schema_menu_locator
            )
        ).click()

        # Click 'multiselect_dropdown' drop-down menu
        wait.until(
            EC.visibility_of_element_located(
                search_page_helpers.includes_community_schema_multiselect_dropdown_selector
            )
        ).click()

        search_page_helpers.check_search_in_filtering_options(driver)

    def test_sorting_by_created_date_on_files_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # search_page_short.loading_indicator.here_then_gone()
        # Switch to the Files Tab
        open_files_tab(driver, search_page_helpers)
        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_sorting_by_created_date(driver, 'created')

    def test_sorting_by_modified_date_on_files_tab(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        # search_page.loading_indicator.here_then_gone()
        # Switch to the Files Tab
        open_files_tab(driver, search_page_helpers)

        search_page_helpers.skip_if_no_results(driver)
        search_page_helpers.check_sorting_by_modified_date(driver)

    def test_search_card_files(
        self,
        driver,
        must_be_logged_in_as_profile_user,
        profile_page_short,
        search_page_helpers,
    ):
        wait_until_page_ready(driver)
        search_page_helpers.files_tab_link.click()
        wait_until_page_ready(driver)
        _validate_file_card(driver, FileSearchResults(driver))


@markers.dont_run_on_prod
@markers.core_functionality
@pytest.mark.usefixtures('must_be_logged_in')
class TestUserSocialLinks:

    testable_links = [
        'github',
        'linkedin',
        'researcherid',
        'x',
        'impactstory',
        'googlescholar',
        'researchgate',
        'baiduscholar',
        'ssrn',
        'yourwebsite',
    ]

    LINK_ID_MAP = {
        'github': 'osframeworktesting',
        'linkedin': 'in/openscienceframework-test-29b4a8408/',
        'researcherid': 'S-1234-6789',
        'x': 'OsfTesting',
        'googlescholar': 'TEST12345',
        'impactstory': 'IMP-12345',
        'researchgate': 'osframeworktesting/selenium.testing:',
        'baiduscholar': 'CN-TEST123',
        'ssrn': '100-234-7896',
        'yourwebsite': 'https://mywebapp.com',
        'academia': 'collection:personal:7PZSFFBN',
    }

    def get_link_id(self, social_link):
        return self.LINK_ID_MAP.get(social_link)

    LINK_PLACEHOLDER_MAP = {
        'github': 'username',
        'linkedin': 'in/userID, profie/view?profileID, or pub/pubID',
        'researcherid': 'x-xxxx-xxxx',
        'x': 'twitterhandle',
        'googlescholar': 'profileID',
        'impactstory': 'profileID',
        'researchgate': 'profileID',
        'baiduscholar': 'profileID',
        'ssrn': 'profileID',
        'yourwebsite': 'https://yourwebsite.com',
        'academia': 'profileId',
    }

    def get_placeholder_text(self, social_link):
        return self.LINK_PLACEHOLDER_MAP.get(social_link)

    LINK_LOGO_MAP = {
        'github': 'github.svg',
        'linkedin': 'linkedin.svg',
        'researcherid': 'researcherID.png',
        'x': 'x.svg',
        'googlescholar': 'scholar.svg',
        'impactstory': 'impactstory.png',
        'researchgate': 'researchGate.svg',
        'baiduscholar': 'baiduScholar.png',
        'ssrn': 'ssrn.svg',
        'yourwebsite': 'globe.svg',
        'academia': 'profileId',
    }

    def get_link_logo(self, social_link):
        return self.LINK_LOGO_MAP.get(social_link)

    @pytest.mark.parametrize('social_link', testable_links)
    def test_profile_links(self, session, driver, profile_page_short, social_link):
        try:
            wait_until_page_ready(driver)
            user_name = profile_page_short.profile_name.text.strip()
            link_id = self.get_link_id(social_link)
            placeholder_text = self.get_placeholder_text(social_link)
            profile_page_short.click_on_button('Edit Profile')
            utils.wait_until_page_ready(driver)
            profile_page_short.select_profile_tab('Social')
            if social_link in [
                'googlescholar',
                'impactstory',
                'researchgate',
                'baiduscholar',
                'ssrn',
            ]:
                profile_page_short.send_social_link_input_profile_id(
                    social_link, link_id=link_id
                )
            else:
                profile_page_short.send_social_link_input(link_id, placeholder_text)

            element = driver.find_element(
                By.XPATH, '//button[.//span[normalize-space()="Save"]]'
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });",
                element,
            )
            profile_page_short.click_on_save_button('Social')
            utils.wait_until_page_ready(driver)
            profile_page = ProfilePage(driver)
            profile_page.goto()
            utils.wait_until_page_ready(driver)

            expected_logo = self.get_link_logo(social_link)
            actual_logo_src = profile_page.get_social_link_logo(social_link)
            assert expected_logo in actual_logo_src
        finally:
            osf_api.update_user_social(session, user_name)

    def test_profile_link(self, session, driver, profile_page_short):
        """This test verifies link to profile and date created"""
        wait_until_page_ready(driver)
        created_date = profile_page_short.profile_created_date.text.strip()
        user_name = profile_page_short.profile_name.text.strip()
        # Get user details from api
        user_data = osf_api.get_user_details(session, user_name)
        api_registered_date = user_data['data']['attributes']['date_registered']
        user_guid = user_data['data']['id']
        ui_date = utils.extract_ui_date(created_date)
        # Verify that UI registered date matches with api registered date
        assert ui_date == datetime.fromisoformat(api_registered_date).date()

        user_profile_link = profile_page_short.profile_link.text.strip()
        assert user_guid in user_profile_link
