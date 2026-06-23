import time

import pytest
from pythosf import client
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

import markers
import settings
from api import osf_api
from components import navbars
from pages.base import BasePage  # ProjectPage,
from pages.project import MyProjectsPage


@pytest.fixture()
def my_projects_page(driver):
    my_projects_page = MyProjectsPage(driver)
    # projects_page.goto()
    return my_projects_page


@markers.dont_run_on_prod
@pytest.mark.usefixtures('must_be_logged_in')
class TestMyProjectsPage:
    """Custom collections must implement a PRE-delete setup to start in a clean state."""

    def wait_until_page_ready(self, driver, timeout=30):
        wait = WebDriverWait(driver, timeout)

        wait.until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'p-progress-spinner'))
        )

    def wait_for_table_first_row(self, driver, timeout=20):
        wait = WebDriverWait(driver, timeout)

        # 1. Wait for the skeleton row to appear
        skeleton_locator = (By.XPATH, '//tr[contains(@class, "loading-row")]')
        try:
            wait.until(EC.visibility_of_element_located(skeleton_locator))
        except TimeoutException:
            pass

        # 2. Wait for the skeleton row to disappear
        wait.until(EC.invisibility_of_element_located(skeleton_locator))

        # 3. Wait for the first real row to appear
        first_row_locator = (
            By.CSS_SELECTOR,
            'tbody.p-datatable-tbody > tr',
        )
        wait.until(EC.visibility_of_element_located(first_row_locator))

    def wait_until_spinner_disappears(self, driver, timeout=15):
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'p-progress-spinner'))
        )

    def open_my_projects(self, driver, wait):
        navbar = navbars.EmberNavbar(driver)
        navbar.my_osf_link.click()
        navbar.my_projects_link.click()
        self.wait_for_table_first_row(driver)

        wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    '//input[@placeholder="Filter by title, description, and tags"]',
                )
            )
        )
        wait.until(EC.visibility_of_element_located((By.XPATH, '//table//tbody/tr[1]')))

    @pytest.fixture
    def registration_user_session(self):
        return client.Session(
            api_base_url=settings.API_DOMAIN,
            auth=(settings.USER_ONE, settings.USER_ONE_PASSWORD),
        )

    @pytest.fixture
    def create_projects(self, registration_user_session, fake):
        prefixes = [
            '1 OSF Reg Project',
            '2 OSF Reg Project',
            'ZZZ OSF Reg Project',
        ]

        projects = []
        titles = []

        for prefix in prefixes:
            random_suffix = fake.pystr(min_chars=5, max_chars=10).lower()
            project_title = f'{prefix} {random_suffix}'

            project = osf_api.create_project(
                registration_user_session,
                title=project_title,
                tags=['qa_project_tag', '2qa_tag'],
                description='QA test description',
            )

            projects.append(project)
            titles.append(project_title)

        yield titles

        for project in projects:
            project.delete()

    @pytest.fixture
    def create_single_project(self, registration_user_session, fake):
        prefix = 'AQA Reg Project withComponent'
        random_suffix = fake.pystr(min_chars=5, max_chars=10).lower()
        title = f'{prefix} {random_suffix}'

        project = osf_api.create_project(
            registration_user_session,
            title=title,
            tags=['qa_project_tag', '2qa_tag'],
            description='QA test description',
        )

        yield {'title': title, 'project': project}

        project.delete()

    @pytest.fixture
    def create_component_in_project(
        self, registration_user_session, create_single_project
    ):
        project = create_single_project['project']

        child_node = osf_api.create_child_node(
            session=registration_user_session,
            node=project,
            title='Child component title',
            tags=['child tag'],
        )

        yield child_node

        osf_api.delete_project(registration_user_session, guid=child_node.id)

    def test_create_new_project(self, driver, session, my_projects_page, fake):
        actions = ActionChains(driver)

        wait = WebDriverWait(driver, 10)
        title = fake.sentence(nb_words=4)

        my_projects_page.create_project_button.click()
        create_project_modal = my_projects_page.create_project_modal
        create_project_modal.title_input.clear()
        create_project_modal.title_input.send_keys(title)

        dropdown_trigger = wait.until(
            ec.visibility_of_element_located((By.ID, 'storage-location'))
        )
        time.sleep(1)
        actions.move_to_element(dropdown_trigger).click().perform()

        first_option = wait.until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, 'ul#storage-location_list li.p-select-option')
            )
        )

        first_option.click()

        create_project_modal.create_project_button.click()

        # Wait until modal is gone
        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, 'button[data-dismiss="modal"]')
            )
        )

        first_element = wait.until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, 'td span.overflow-ellipsis'))
        )
        assert first_element.is_displayed()
        created_project_row = wait.until(
            ec.element_to_be_clickable((By.XPATH, f"//span[text()='{title}']"))
        )

        assert title in created_project_row.text
        wait.until(
            ec.visibility_of_element_located(
                (By.CSS_SELECTOR, 'button.p-button.p-dialog-close-button')
            )
        ).click()

        wait.until(
            ec.invisibility_of_element_located(
                (By.CSS_SELECTOR, 'button.p-button.p-dialog-close-button')
            )
        )
        created_project_row.click()

        # Check if title displays correct name
        assert wait.until(
            ec.visibility_of_element_located((By.XPATH, f'//h1[text()=" {title} "]'))
        ).is_displayed()

        # Delete the project as cleanup
        current_url = driver.current_url
        project_guid = current_url.split('/')[4]
        osf_api.delete_project(session, project_guid, None)

    def test_filter_project_by_title(
        self, driver, session, create_projects, my_projects_page, fake
    ):
        wait = WebDriverWait(driver, 10)
        self.open_my_projects(driver, wait)
        target_title = create_projects[0]
        second_title = create_projects[1]
        third_title = create_projects[2]
        my_projects_page.filters_input_field.send_keys(target_title)

        # wait until skeleton disappeared and first row in the table will be visible
        my_projects_page.wait_for_first_row_title(target_title)

        wait.until(
            EC.invisibility_of_element_located((By.XPATH, '//table//tbody/tr[3]'))
        )

        # Check that project 'target_title' is displayed in filtering results
        assert my_projects_page.is_record_visible_in_table(target_title)

        # Check that project 'second_title', 'third_title' aren't displayed in filtering results
        assert not my_projects_page.is_record_visible_in_table(second_title)
        assert not my_projects_page.is_record_visible_in_table(third_title)

    def test_filter_project_by_description(
        self, driver, session, create_projects, my_projects_page, fake
    ):
        wait = WebDriverWait(driver, 10)
        self.open_my_projects(driver, wait)
        target_title = create_projects[2]

        # Input data is filter input
        my_projects_page.filters_input_field.send_keys('QA test description')

        # wait until skeleton disappeared and first row in the table will be visible
        my_projects_page.wait_for_first_row_title(target_title)

        # Check that project 'Ztarget_title' with description 'QA test description' is displayed in filtering results
        assert my_projects_page.is_record_visible_in_table(target_title)

        # Check number of displayed results
        visible_project = driver.find_elements(By.XPATH, '//table//tbody/tr')

        assert len(visible_project) >= 3

    def test_filter_project_by_tag(
        self, driver, session, create_projects, my_projects_page, fake
    ):
        wait = WebDriverWait(driver, 10)
        self.open_my_projects(driver, wait)
        target_title = create_projects[2]

        my_projects_page.filters_input_field.send_keys('qa_project_tag')

        # wait until skeleton disappeared and first row in the table will be visible
        my_projects_page.wait_for_first_row_title(target_title)

        # Check that project 'target_title' with tag 'qa_project_tag' is displayed in filtering results
        assert my_projects_page.is_record_visible_in_table(target_title)

        # Check number of displayed results
        visible_project = driver.find_elements(By.XPATH, '//table//tbody/tr')

        assert len(visible_project) >= 3

    def test_sort_projects_by_title(
        self, driver, session, create_projects, my_projects_page, fake
    ):
        wait = WebDriverWait(driver, 10)
        project_list = my_projects_page
        self.open_my_projects(driver, wait)
        target_title = create_projects[0]
        third_title = create_projects[2]
        my_projects_page.filters_input_field.send_keys('OSF Reg Project')
        wait.until(EC.visibility_of_element_located((By.XPATH, '//table//tbody/tr[1]')))

        title_sorting_icon = wait.until(
            ec.visibility_of_element_located(
                my_projects_page.title_sorting_icon_locator
            )
        )
        title_sorting_icon.click()

        # wait until sorting will be applied and correct row appears
        my_projects_page.wait_for_first_row_title(target_title)
        assert project_list.sort_title_asc_button.is_displayed()

        elements = my_projects_page.wait_for_rows_with_title('OSF Reg Project')

        titles = [el.text.strip() for el in elements]
        assert titles == sorted(titles), f'Titles are not sorted ASC: {titles}'

        project_list.sort_title_asc_button.click()

        # wait until sorting will be applied and correct row appears
        my_projects_page.wait_for_first_row_title(third_title)
        elements = my_projects_page.wait_for_rows_with_title('OSF Reg Project')

        titles = [el.text.strip() for el in elements]
        assert titles == sorted(
            titles, reverse=True
        ), f'Titles are not sorted DESC: {titles}'

    def test_sort_projects_by_modified(
        self, driver, session, create_projects, my_projects_page, fake
    ):
        wait = WebDriverWait(driver, 15)
        project_list = my_projects_page
        base_page = BasePage(driver)
        self.open_my_projects(driver, wait)

        my_projects_page.filters_input_field.send_keys('OSF Reg Project')

        modified_sorting_icon = wait.until(
            EC.visibility_of_element_located(project_list.modified_sorting_icon_locator)
        )

        # click modified sorting icon
        modified_sorting_icon.click()
        time.sleep(4)
        self.wait_until_page_ready(driver)
        self.wait_for_table_first_row(driver)
        # Check if appropriate sorting buttons appears.
        assert project_list.sort_date_asc_button.is_displayed()

        # Check if table content sorted correctly by modified column.
        dates = base_page.get_modified_dates_from_table()
        base_page.assert_sorting(dates, order='ascending')
        # project_list.assert_sorted_by_modified(order='ascending')

        # Click 'modified' sorting button one more time
        project_list.sort_date_asc_button.click()
        self.wait_for_table_first_row(driver)

        # Check if table content sorted correctly by modified column.
        assert project_list.sort_date_dsc_button.is_displayed()
        dates = base_page.get_modified_dates_from_table()
        base_page.assert_sorting(dates, order='descending')

    def test_selection_of_project_or_component(
        self,
        driver,
        session,
        create_component_in_project,
        create_single_project,
        my_projects_page,
        fake,
    ):
        wait = WebDriverWait(driver, 10)
        self.open_my_projects(driver, wait)

        project_title = create_single_project['title']
        component_title = 'Child component title'

        # 1. Select 'Projects only'
        dropdown = wait.until(
            EC.element_to_be_clickable(my_projects_page.filter_type_dropdown_locator)
        )
        dropdown.click()

        projects = wait.until(
            EC.element_to_be_clickable(my_projects_page.projects_only_option_locator)
        )
        projects.click()

        my_projects_page.wait_for_first_row_title(project_title)

        # 2. Only projects visible
        assert my_projects_page.is_record_visible_in_table(project_title)

        # 3. Components should not be visible
        assert not my_projects_page.is_record_visible_in_table(component_title)

        # 4. Select 'Components only'
        dropdown.click()

        components = wait.until(
            EC.element_to_be_clickable(my_projects_page.components_only_option_locator)
        )
        components.click()

        my_projects_page.wait_for_first_row_title(component_title)

        # 5. Only components visible
        assert my_projects_page.is_record_visible_in_table(component_title)
        assert not my_projects_page.is_record_visible_in_table(project_title)
