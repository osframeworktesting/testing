import time
from datetime import datetime

import pytest
from faker import Faker
from pythosf import client
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import markers
import settings
from api import osf_api
from components import navbars
from pages.base import BasePage

# from pages.preprints import MyPreprintsPage
from pages.preprints import (
    MyPreprintsPage,
    NewPreprintsProviderServicePage,
    PreprintLandingPage,
    PreprintSubmitPage,
)


@pytest.fixture()
def my_preprints_page(driver):
    my_preprints_page = MyPreprintsPage(driver)
    return my_preprints_page


@pytest.fixture
def landing_page(driver):
    landing_page = PreprintLandingPage(driver)
    landing_page.goto()
    return landing_page


@pytest.fixture
def project_with_file_reg(registration_user_session, fake):
    """Returns a project with a file using the login session of the Registrations User."""

    prefix = 'OSF Reg Project with file fpp'
    random_suffix = fake.pystr(min_chars=5, max_chars=10).lower()
    title = f'{prefix} {random_suffix}'

    project = osf_api.create_project(
        registration_user_session,
        title=title,
    )

    osf_api.upload_fake_file(
        registration_user_session,
        project,
        name='osf selenium test file for preprints.txt',
    )

    yield {
        'title': title,
        'project': project,
    }

    project.delete()


@markers.dont_run_on_prod
@pytest.mark.usefixtures('must_be_logged_in')
class TestMyPreprintsPage:
    fake = Faker()

    def scroll_footer(self, driver):
        footer = driver.find_element(By.CSS_SELECTOR, 'osf-footer')
        driver.execute_script(
            "arguments[0].scrollIntoView({ block: 'center' });",
            footer,
        )

    def wait_next_clickable(self, driver, timeout=20):
        wait = WebDriverWait(driver, timeout)
        wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[normalize-space(text())='Next']]")
            )
        )

    def wait_until_page_ready(self, driver, timeout=30):
        wait = WebDriverWait(driver, timeout)

        wait.until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'p-progress-spinner'))
        )
        time.sleep(1)

    def wait_for_table_first_row(self, driver, timeout=5):
        wait = WebDriverWait(driver, timeout)

        # 1. Wait for the skeleton row to appear
        skeleton_locator = (By.XPATH, '//tr[contains(@class, "loading-row")]')
        try:
            wait.until(EC.visibility_of_element_located(skeleton_locator))
        except TimeoutException:
            pass

        # 2. Wait for the skeleton row to disappear
        wait.until(EC.invisibility_of_element_located(skeleton_locator))
        self.wait_until_page_ready(driver)

        # 3. Wait for the first real row to appear
        first_row_locator = (
            By.XPATH,
            '//table//tbody/tr[contains(@class, "cursor-pointer")][1]',
        )
        try:
            wait.until(EC.visibility_of_element_located(first_row_locator))
        except TimeoutException:
            pass

    def open_my_preprints(self, driver, wait):
        navbar = navbars.EmberNavbar(driver)
        navbar.my_osf_link.click()
        navbar.my_preprints_link.click()

        self.wait_for_table_first_row(driver)
        wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    '//input[@placeholder="Filter by title, description, and tags"]',
                )
            )
        )

    @pytest.fixture
    def registration_user_session(self):
        return client.Session(
            api_base_url=settings.API_DOMAIN,
            auth=(settings.USER_ONE, settings.USER_ONE_PASSWORD),
        )

    @pytest.fixture
    def create_preprints(self, registration_user_session, fake):
        prefixes = ['1 OSF Preprint', '2 OSF Preprint', 'ZZZ OSF Preprint']
        provider_id = 'selpostmod'

        titles = []
        for prefix in prefixes:
            random_suffix = fake.pystr(min_chars=5, max_chars=10).lower()
            preprint_title = f'{prefix} {random_suffix}'
            osf_api.create_preprint(
                registration_user_session,
                provider_id=provider_id,
                title=preprint_title,
                license_name='CC0 1.0 Universal',
                subject_name='Engineering',
            )
            titles.append(preprint_title)

        yield titles

    @pytest.fixture
    def create_single_preprint(self, registration_user_session, fake):
        provider_id = 'selpostmod'
        preprint_title = f'AQA Reg SinglePreprint {fake.word().capitalize()}'

        osf_api.create_preprint(
            registration_user_session,
            provider_id=provider_id,
            title=preprint_title,
            license_name='CC0 1.0 Universal',
            subject_name='Engineering',
        )

        yield preprint_title

    def test_filter_preprints_by_title(
        self, driver, session, create_preprints, my_preprints_page, fake
    ):
        wait = WebDriverWait(driver, 25)
        self.open_my_preprints(driver, wait)
        target_title = create_preprints[0]
        second_title = create_preprints[1]
        third_title = create_preprints[2]

        my_preprints_page.filters_input_field.send_keys(target_title)

        my_preprints_page.wait_for_row_with_title_invisible(second_title)
        my_preprints_page.wait_for_first_row_title(target_title)

        # Check that other preprints are not displayed
        assert not my_preprints_page.is_preprint_visible(second_title)
        assert not my_preprints_page.is_preprint_visible(third_title)

        # Check that the target preprint is visible
        assert my_preprints_page.is_preprint_visible(target_title)

    def test_filter_preprints_by_tag(
        self, driver, session, create_preprints, my_preprints_page, fake
    ):
        wait = WebDriverWait(driver, 25)
        self.open_my_preprints(driver, wait)

        target_title = create_preprints[0]
        second_title = create_preprints[1]
        third_title = create_preprints[2]

        my_preprints_page.filters_input_field.send_keys('AQA preprint tag')
        self.wait_until_page_ready(driver)

        # wait until skeleton disappeared and first row in the table will be visible
        my_preprints_page.wait_for_first_row_title(third_title)

        # Check that preprints 'target_title', 'second_title', 'third_title' with tag 'AQA preprint tag' are displayed in filtering results
        assert my_preprints_page.is_preprint_visible(target_title)
        assert my_preprints_page.is_preprint_visible(second_title)
        assert my_preprints_page.is_preprint_visible(third_title)

        # Check number of displayed results
        visible_preprint = driver.find_elements(By.XPATH, '//table//tbody/tr')

        assert len(visible_preprint) >= 3

    def test_filter_preprints_by_description(
        self, driver, session, create_preprints, my_preprints_page, fake
    ):
        wait = WebDriverWait(driver, 25)
        self.open_my_preprints(driver, wait)
        target_title = create_preprints[2]

        # Input data is filter input
        my_preprints_page.filters_input_field.send_keys(
            'Preprint created via the OSF api'
        )
        self.wait_until_page_ready(driver)

        # wait until skeleton disappeared and first row in the table will be visible
        my_preprints_page.wait_for_first_row_title(target_title)

        # Check that preprint 'target_title' with description 'Preprint created via the OSF api' is displayed in filtering results
        assert my_preprints_page.is_preprint_visible(target_title)

        # Check number of displayed results
        visible_preprint = driver.find_elements(By.XPATH, '//table//tbody/tr')

        assert len(visible_preprint) >= 3

    def test_sort_preprints_by_title(
        self, driver, session, create_preprints, my_preprints_page, fake
    ):
        wait = WebDriverWait(driver, 30)
        preprint_list = my_preprints_page
        self.open_my_preprints(driver, wait)
        my_preprints_page.filters_input_field.send_keys('OSF Preprint')
        wait.until(EC.visibility_of_element_located((By.XPATH, '//table//tbody/tr[1]')))

        title_sorting_icon = wait.until(
            EC.element_to_be_clickable(my_preprints_page.title_sorting_icon_locator)
        )
        self.wait_for_table_first_row(driver)
        title_sorting_icon.click()

        # wait until sorting will be applied and correct row appears

        assert preprint_list.sort_title_asc_button.is_displayed()

        elements = my_preprints_page.wait_for_rows_with_title('OSF Preprint')

        titles = [el.text.strip() for el in elements]
        assert titles == sorted(titles), f'Titles are not sorted ASC: {titles}'

        preprint_list.sort_title_asc_button.click()

        # wait until sorting will be applied and correct row appears
        self.wait_for_table_first_row(driver)
        elements = my_preprints_page.wait_for_rows_with_title('OSF Preprint')

        titles = [el.text.strip() for el in elements]
        assert titles == sorted(
            titles, reverse=True
        ), f'Titles are not sorted DESC: {titles}'

    def test_sort_preprints_by_modified(
        self, driver, session, create_preprints, my_preprints_page, fake
    ):

        wait = WebDriverWait(driver, 25)
        base_page = BasePage(driver)
        preprint_list = my_preprints_page
        self.open_my_preprints(driver, wait)

        my_preprints_page.filters_input_field.send_keys('OSF Preprint')
        self.wait_for_table_first_row(driver)
        modified_sorting_icon = wait.until(
            EC.visibility_of_element_located(
                my_preprints_page.modified_sorting_icon_locator
            )
        )

        # click modified sorting icon
        modified_sorting_icon.click()

        self.wait_for_table_first_row(driver)
        # Check if appropriate sorting buttons appears.
        assert preprint_list.sort_date_asc_button.is_displayed()

        # Check if table content sorted correctly by modified column.
        dates = base_page.get_modified_dates_from_table()
        base_page.assert_sorting(dates, order='ascending')

        # Click 'modified' sorting button one more time
        preprint_list.sort_date_asc_button.click()
        self.wait_for_table_first_row(driver)

        # Check if table content sorted correctly by modified column.
        assert preprint_list.sort_date_dsc_button.is_displayed()
        dates = base_page.get_modified_dates_from_table()
        base_page.assert_sorting(dates, order='descending')

    def test_create_preprint_on_my_preprints(
        self, driver, session, project_with_file_reg, my_preprints_page, fake
    ):
        wait = WebDriverWait(driver, 30)
        self.open_my_preprints(driver, wait)
        supplemental_guid = None
        project_name = project_with_file_reg['title']
        preprint_prefix = 'AQA Test Preprint'
        random_suffix = fake.pystr(min_chars=5, max_chars=10).lower()
        preprint_title = f'{preprint_prefix} {random_suffix}'
        try:
            landing_page = PreprintLandingPage(driver, verify=True)
            # Create a date and time stamp before starting the creation of the preprint.
            # This may be used later to find the guid for the preprint.
            now = datetime.utcnow()
            date_time_stamp = now.strftime('%Y-%m-%dT%H:%M:%S')
            # need to figure why this locator needs to be added manually
            landing_page.add_preprint_button = driver.find_element(
                By.XPATH, '//button[.//span[normalize-space(text())="Add a Preprint"]]'
            )

            landing_page.add_preprint_button.click()
            # Select provider service
            select_provider_page = NewPreprintsProviderServicePage(driver, verify=True)
            providers_list = driver.find_elements_by_css_selector(
                'p-card.provider-card'
            )
            for provider in providers_list:
                if 'AfricArXiv' in provider.text:
                    select_provider_page.scroll_into_view(provider)
                    # provider.click()
                    provider.find_element_by_css_selector(
                        'button.p-button.p-button-secondary'
                    ).click()
                    break

            self.scroll_footer(driver)
            self.wait_next_clickable(driver)

            select_provider_page.next_button.click()
            submit_page = PreprintSubmitPage(driver)
            # Title and Abstract
            self.wait_until_page_ready(driver)
            wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        '//label[normalize-space(text())="Title"]/following-sibling::input',
                    )
                )
            )

            submit_page.preprint_title_input.click()
            submit_page.preprint_title_input.send_keys(preprint_title)
            submit_page.abstract_input.click()
            submit_page.abstract_input.send_keys('Center for Open Selenium')
            self.scroll_footer(driver)
            self.wait_next_clickable(driver)

            submit_page.next_button.click()
            submit_page.info_toast.here_then_gone()
            self.wait_until_page_ready(driver)
            # File Upload
            submit_page.upload_from_existing_project_button.click()
            submit_page.upload_project_selector.click()
            submit_page.upload_project_help_text.here_then_gone()
            self.wait_until_page_ready(driver)

            wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'input[placeholder = "Project Title"]')
                )
            )

            submit_page.project_selector_input.send_keys(project_name)

            wait.until(EC.element_to_be_clickable((By.ID, 'project-select_list')))

            option = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        f'//li[@role="option"]//span[normalize-space(text())="{project_name}"]/ancestor::li',
                    )
                )
            )

            option.click()

            self.wait_until_page_ready(driver)
            # submit_page.upload_project_selector_project.click()
            submit_page.scroll_into_view(submit_page.upload_select_file.element)
            # time.sleep(1)
            wait.until(EC.visibility_of(submit_page.upload_select_file))
            submit_page.upload_select_file.click()
            self.scroll_footer(driver)
            self.wait_next_clickable(driver)
            submit_page.next_button.click()

            # Metadata page
            wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//h2[normalize-space(text())="Metadata"]')
                )
            )

            driver.execute_script(
                "arguments[0].scrollIntoView({ block: 'center' });",
                submit_page.basics_license_dropdown.element,
            )
            submit_page.basics_license_dropdown.click()
            # The order of the options in the license dropdown is not consistent across
            # test environments. So we have to select by the actual text value instead
            # of by relative position (i.e. 3rd option in listbox).
            self.wait_until_page_ready(driver)
            # wait.until(EC.element_to_be_clickable(submit_page.select_from_dropdown_listbox))
            submit_page.select_from_dropdown_listbox('CC0 1.0 Universal')
            submit_page.scroll_into_view(submit_page.basics_tags_section.element)
            submit_page.select_top_level_subject('Engineering')
            wait.until(EC.visibility_of(submit_page.first_selected_subject))
            assert submit_page.first_selected_subject.text == 'Engineering'

            # Need to scroll down since the Keyword/tags section is obscured by the Dev
            # mode warning in the test environments
            submit_page.scroll_into_view(submit_page.basics_tags_input.element)
            submit_page.basics_tags_input.click()
            submit_page.basics_tags_input.send_keys('selenium\r')

            submit_page.scroll_into_view(submit_page.next_button.element)
            self.scroll_footer(driver)
            self.wait_next_clickable(driver)
            submit_page.next_button.click()

            # Author Assertions section
            # Note: We can't use the submit_page.save_author_assertions object here,
            # because it is disabled and any time we use an object defined in
            # pages/preprints.py it uses get_web_element() in the Locator class.
            # Within get_web_element() the element_to_be_clickable method is used,
            # and this method will always fail for disabled objects.  So in this
            # instance we have to get the button object using the driver.find_element
            # method while it is disabled.  After the button becomes enabled (i.e.
            # after required data has been provided) then we can use the
            # submit_page.save_author_assertions object to check the disabled
            # property.  See implementation below.
            assert driver.find_element(
                By.XPATH, '//button[.//span[normalize-space(text())="Next"]]'
            ).get_property('disabled')

            self.wait_until_page_ready(driver)

            # Conflict of Interest section:
            self.wait_until_page_ready(driver)
            wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//h2[normalize-space(text())="Conflict of Interest"]')
                )
            )
            submit_page.info_toast.here_then_gone()
            submit_page.conflict_of_interest_yes.click()
            assert submit_page.coi_text_box.present()
            submit_page.coi_text_box.click()
            submit_page.coi_text_box.send_keys_deliberately('QA Testing')
            # assert submit_page.public_data_input.absent()
            submit_page.scroll_into_view(submit_page.public_available_button.element)
            submit_page.public_available_button.click()
            assert submit_page.public_data_input.present()
            submit_page.scroll_into_view(submit_page.add_another_public_data.element)
            submit_page.public_data_input.click()
            submit_page.public_data_input.send_keys_deliberately('https://osf.io/')
            # Need to scroll down since the Preregistration radio buttons are obscured
            # by the Dev mode warning in test environments
            # submit_page.scroll_into_view(submit_page.preregistration_no_button.element)
            # assert submit_page.preregistration_input.absent()
            submit_page.preregistration_no_button.click()
            assert submit_page.preregistration_input.present()
            submit_page.scroll_into_view(submit_page.preregistration_input.element)
            submit_page.preregistration_input.click()
            submit_page.preregistration_input.send_keys_deliberately('QA Testing')
            submit_page.scroll_into_view(submit_page.next_button.element)
            self.scroll_footer(driver)
            # Next button is now enabled so that we can use the object as defined in
            # pages/preprints.py
            assert submit_page.next_button.is_enabled()
            submit_page.next_button.click()

            # Wait for Supplemental materials to show
            submit_page.supplemental_create_new_project.click()
            submit_page.supplemental_project_title.click()
            submit_page.supplemental_project_title.send_keys_deliberately(
                'Selenium Test Project'
            )
            # submit_page.supplemental_project_create_button.click()
            submit_page.info_toast.here_then_gone()
            self.scroll_footer(driver)
            submit_page.next_button.click()
            wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//h2[normalize-space(.)="Consent To Publish"]')
                )
            )

            submit_page.info_toast.here_then_gone()
            self.scroll_footer(driver)
            submit_page.create_preprint_button.click()

            preprint_title_on_page = wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, f'//h1[text()="{preprint_title}"]')
                )
            )

            assert preprint_title_on_page.text.lower() == preprint_title.lower()

            supplemental_element = driver.find_element(
                By.CSS_SELECTOR, 'a.font-bold.flex.gap-1'
            )
            supplemental_url = supplemental_element.get_attribute('href')
            supplemental_guid = supplemental_url.rstrip('/').split('/')[-1]
            print('supplemental_guid', supplemental_guid)

        finally:
            # If there was an error above and we did not capture the guid for the
            # supplemental materials project, then we need to get it if it exists.
            if supplemental_guid is None:
                # Get the list of preprints for the current user
                preprints = osf_api.get_preprints_list_for_user(session)
                for preprint in preprints:
                    # Go through the list of preprints and if any of them has a creation
                    # date and time after the date time stamp that we created before
                    # starting this preprint then that is our preprint, so use its guid
                    # to get the guid for the supplemental materials project.
                    if preprint['attributes']['date_created'] > date_time_stamp:
                        supplemental_guid = (
                            osf_api.get_preprint_supplemental_material_guid(
                                session, preprint['id']
                            )
                        )
                        break

            # We need to always delete the supplemental materials project if it exists
            if supplemental_guid is not None:
                osf_api.delete_project(session, supplemental_guid, None)

            # If we are still stuck on the Preprint Submit page then refresh it to see
            # if we get an alert pop-up message about leaving the page.  If so then
            # accept the alert so that we can get off this page and can proceed with
            # the rest of the tests.
            # if submit_page.verify():
            #     submit_page.reload()
            #     try:
            #         WebDriverWait(driver, 3).until(EC.alert_is_present())
            #         driver.switch_to.alert.accept()
            #     except TimeoutException:
            #         pass
