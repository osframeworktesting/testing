import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import markers
import settings
import utils
from api import osf_api
from pages.project import ContributorsPage


@pytest.mark.usefixtures('must_be_logged_in')
@markers.core_functionality
class TestProjectContributors:
    @pytest.fixture()
    def project_contributors_page(self, driver, default_project):
        project_contributors_page = ContributorsPage(driver, guid=default_project.id)
        project_contributors_page.goto()
        return project_contributors_page

    @pytest.fixture()
    def project_contributors_page_with_contributors(
        self, driver, default_project_with_contributors
    ):
        project_contributors_page_with_contributors = ContributorsPage(
            driver, guid=default_project_with_contributors.id
        )
        project_contributors_page_with_contributors.goto()
        return project_contributors_page_with_contributors

    def test_add_contributors(
        self, session, driver, project_contributors_page, default_project
    ):
        """This test verifies that user can add/remove
        contributors to registration metadata."""

        if settings.DOMAIN == 'prod':
            new_user = 'OSF Tester1'
        else:
            new_user = 'OSF Runscope Admin'

        # Delete the user if its already exists
        osf_api.delete_project_contributor(
            session, node_id=default_project.id, user_name=new_user
        )
        contributors_list = project_contributors_page.get_contributors_list()
        assert new_user not in contributors_list
        project_contributors_page.click_on_button('Add Contributor')
        utils.wait_until_page_ready(driver)
        time.sleep(2)
        project_contributors_page.add_contributors_modal.search_input.clear()
        project_contributors_page.add_contributors_modal.search_input.send_keys(
            new_user
        )
        project_contributors_page.add_contributors_modal.select_contributor_checkbox_by_name(
            new_user
        )
        project_contributors_page.add_contributors_modal.click_on_next()
        project_contributors_page.add_contributors_modal.click_on_button('Done')

        # Check that modal window contains new user
        project_contributors_page.reload()
        utils.wait_until_page_ready(driver)
        new_contributors_list = project_contributors_page.get_contributors_list()
        assert new_user in new_contributors_list
        project_contributors_page.reload()
        utils.wait_until_page_ready(driver)
        project_contributors_page.search_input.clear()
        project_contributors_page.search_input.send_keys(new_user)
        assert project_contributors_page.contributor_name.text.strip() == new_user

    def test_edit_contributor_permission(
        self, driver, session, project_contributors_page_with_contributors
    ):
        """This test verifies that user can update permissions for
        contributors on a  Project Contributors."""

        contributor_name = 'OSF Runscope Admin'
        new_permission = 'Administrator'

        # Get contributors list for a registration
        contributors_list = (
            project_contributors_page_with_contributors.get_contributors_list()
        )
        # Verify that given contributor_name present in the list
        assert contributor_name in contributors_list
        # Edit contributors
        utils.wait_until_page_ready(driver)
        # Search for the contributor for which permissions need to be updated
        project_contributors_page_with_contributors.search_input.clear()
        project_contributors_page_with_contributors.search_input.send_keys(
            contributor_name
        )
        original_permission = (
            project_contributors_page_with_contributors.user_permission.text.strip()
        )
        assert original_permission != new_permission
        project_contributors_page_with_contributors.select_permission_from_dropdown_listbox(
            new_permission
        )
        project_contributors_page_with_contributors.click_on_button('Save')
        permission_after_change = (
            project_contributors_page_with_contributors.user_permission.text.strip()
        )
        # Verify that user permissions are changed successfully
        assert permission_after_change == new_permission
        # Verify filtering with permission and user is present in filtered list
        project_contributors_page_with_contributors.select_permission_filter_from_dropdown_list(
            new_permission
        )
        admin_filtered_list = (
            project_contributors_page_with_contributors.get_contributors_list()
        )
        assert contributor_name in admin_filtered_list
        # Verify that contributor_name not shown when filtered with other permission filters
        project_contributors_page_with_contributors.select_permission_filter_from_dropdown_list(
            'Read'
        )
        read_filtered_list = (
            project_contributors_page_with_contributors.get_contributors_list()
        )
        assert contributor_name not in read_filtered_list
        # Verify that contributor_name not shown when filtered with other permission filters
        project_contributors_page_with_contributors.reload()
        utils.wait_until_page_ready(driver)
        project_contributors_page_with_contributors.select_permission_filter_from_dropdown_list(
            'Read + Write'
        )
        write_filtered_list = (
            project_contributors_page_with_contributors.get_contributors_list()
        )
        assert contributor_name not in write_filtered_list

    def test_edit_bibliographic_status(
        self, driver, session, project_contributors_page_with_contributors
    ):
        """This test verifies that user can update permissions for
        contributors on a  registration metadata."""

        contributor_name = 'OSF Runscope Admin'

        # Get contributors list for a registration
        project_contributors_page_with_contributors.select_bibliography_filter_from_dropdown_list(
            'Bibliographic'
        )
        contributors_list = (
            project_contributors_page_with_contributors.get_contributors_list()
        )
        # Verify that given contributor_name present in the list
        assert contributor_name in contributors_list
        # Edit contributors bibliographic status
        project_contributors_page_with_contributors.reload()
        utils.wait_until_page_ready(driver)
        # Search for the contributor for which bibliography need to be updated
        project_contributors_page_with_contributors.search_input.clear()
        project_contributors_page_with_contributors.search_input.send_keys(
            contributor_name
        )
        project_contributors_page_with_contributors.click_on_bibliographic_checkbox()
        project_contributors_page_with_contributors.click_on_button('Save')
        project_contributors_page_with_contributors.reload()
        utils.wait_until_page_ready(driver)

        # Verify filtering with bibliographic user filter and user is not present in filtered list
        project_contributors_page_with_contributors.select_bibliography_filter_from_dropdown_list(
            'Bibliographic'
        )
        utils.wait_until_page_ready(driver)
        bibliographic_users = (
            project_contributors_page_with_contributors.get_contributors_list()
        )
        assert contributor_name not in bibliographic_users
        # Verify that contributor_name shown when filtered with Non-Bibliographic user filter
        project_contributors_page_with_contributors.reload()
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    '//span[@aria-label="Bibliography"]/following-sibling::div',
                )
            )
        )
        project_contributors_page_with_contributors.select_bibliography_filter_from_dropdown_list(
            'Non-Bibliographic'
        )
        non_bibliographic_users = (
            project_contributors_page_with_contributors.get_contributors_list()
        )
        assert contributor_name in non_bibliographic_users

    def test_reorder_contributors(
        self,
        driver,
        session,
        project_contributors_page_with_contributors,
        default_project,
    ):
        """This test verifies that user can update permissions for
        contributors on a  registration metadata."""
        contributor_name = 'OSF Runscope Write'
        project_contributors_page_with_contributors.click_on_button('Add Contributor')
        utils.wait_until_page_ready(driver)
        project_contributors_page_with_contributors.add_contributors_modal.search_input.clear()
        project_contributors_page_with_contributors.add_contributors_modal.search_input.send_keys(
            contributor_name
        )
        project_contributors_page_with_contributors.add_contributors_modal.select_contributor_checkbox_by_name(
            contributor_name
        )
        project_contributors_page_with_contributors.add_contributors_modal.click_on_next()
        project_contributors_page_with_contributors.add_contributors_modal.click_on_button(
            'Done'
        )
        utils.wait_until_page_ready(driver)
        source_order = (
            project_contributors_page_with_contributors.get_order_of_contributor(
                contributor_name
            )
        )
        target_order = 1
        rows = driver.find_elements(By.CSS_SELECTOR, 'tbody tr')
        source_element = rows[source_order].find_element(By.CSS_SELECTOR, 'i.fa-bars')
        target_element = rows[target_order].find_element(By.CSS_SELECTOR, 'i.fa-bars')
        utils.drag_and_drop_html5(driver, source_element, target_element)
        project_contributors_page_with_contributors.click_on_button('Save')
        utils.wait_until_page_ready(driver)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    '//h1[text()="Contributors"]',
                )
            )
        )
        project_contributors_page_with_contributors.reload()
        utils.wait_until_page_ready(driver)
        time.sleep(2)
        new_order = (
            project_contributors_page_with_contributors.get_order_of_contributor(
                contributor_name
            )
        )
        assert new_order == target_order

    def test_remove_contributors(
        self, session, driver, project_contributors_page_with_contributors
    ):
        """This test verifies that user can add/remove
        contributors to registration metadata."""

        new_user = 'OSF Runscope Admin'
        contributors_list = (
            project_contributors_page_with_contributors.get_contributors_list()
        )
        assert new_user in contributors_list
        project_contributors_page_with_contributors.goto_with_reload()
        project_contributors_page_with_contributors.search_input.clear()
        project_contributors_page_with_contributors.search_input.send_keys(new_user)
        project_contributors_page_with_contributors.remove_button.click()
        project_contributors_page_with_contributors.click_on_button('Remove')

        # Check that user not shown in contributors list
        utils.wait_until_page_ready(driver)
        contributors_list = (
            project_contributors_page_with_contributors.get_contributors_list()
        )
        assert new_user not in contributors_list
