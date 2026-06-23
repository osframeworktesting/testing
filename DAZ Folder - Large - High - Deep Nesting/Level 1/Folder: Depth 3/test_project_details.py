import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import markers
import settings
import utils
from api import osf_api
from pages.project import (
    ContributorsPage,
    ProjectMetadataPage,
    ProjectPage,
)


@markers.dont_run_on_prod
@pytest.mark.usefixtures('must_be_logged_in')
class TestProjectOverviewLinks:
    @pytest.fixture()
    def project_page(driver, default_project_page):
        default_project_page.goto()
        return default_project_page

    @pytest.fixture()
    def project_details_page(self, driver, default_project_with_all_metadata):
        project_details_page = ProjectPage(
            driver, guid=default_project_with_all_metadata.id
        )
        project_details_page.goto()
        return project_details_page

    @pytest.fixture()
    def project_details_page_metadata(self, driver, default_project_with_metadata):
        project_details_page_metadata = ProjectPage(
            driver, guid=default_project_with_metadata.id
        )
        project_details_page_metadata.goto()
        return project_details_page_metadata

    def test_add_project_link(self, driver, session, project_page, public_link_project):
        """This test verifies add project link to a
        project in overview page functionality."""

        link_project_title = osf_api.get_node_name(session, public_link_project.id)
        project_page.scroll_into_view(project_page.linked_projects_section.element)
        # assert project_page.linked_projects_empty_text.text.strip() == 'Link your project.'
        project_page.click_on_button('Link Projects')
        project_page.link_projects_modal.click_on_button('Projects')
        utils.wait_until_page_ready(driver)
        project_page.link_projects_modal.search_input.clear()
        project_page.link_projects_modal.search_input.send_keys(link_project_title)
        project_page.link_projects_modal.select_project_checkbox_by_name(
            link_project_title
        )
        project_page.link_projects_modal.click_on_button('Done')
        project_page.scroll_into_view(project_page.linked_projects_section.element)
        utils.wait_until_page_ready(driver)
        # Verify that project is linked
        linked_project_list = project_page.get_linked_project_list()
        assert link_project_title in linked_project_list

    def test_add_registration_link(self, driver, session, project_page):
        """This test verifies add registration link to a project in overview page functionality."""

        link_registration_title = 'OSF Link Registration'
        project_page.scroll_into_view(project_page.linked_projects_section.element)
        # assert project_page.linked_projects_empty_text.text.strip() == 'Link your project.'
        project_page.click_on_button('Link Projects')
        project_page.link_projects_modal.click_on_button('Registrations')
        utils.wait_until_page_ready(driver)
        project_page.link_projects_modal.search_input.clear()
        project_page.link_projects_modal.search_input.send_keys(link_registration_title)
        project_page.link_projects_modal.select_project_checkbox_by_name(
            link_registration_title
        )
        project_page.link_projects_modal.click_on_button('Done')
        # Verify that registration is linked
        project_page.scroll_into_view(project_page.linked_projects_section.element)
        linked_project_list = project_page.get_linked_project_list()
        assert link_registration_title in linked_project_list

    def test_remove_project_link(
        self, driver, session, project_page, public_link_project
    ):
        """This test verifies remove project link from a
        project in overview page functionality."""

        link_project_title = osf_api.get_node_name(session, public_link_project.id)
        project_page.scroll_into_view(project_page.linked_projects_section.element)
        project_page.click_on_button('Link Projects')
        project_page.link_projects_modal.click_on_button('Projects')
        utils.wait_until_page_ready(driver)
        project_page.link_projects_modal.search_input.clear()
        project_page.link_projects_modal.search_input.send_keys(link_project_title)
        project_page.link_projects_modal.select_project_checkbox_by_name(
            link_project_title
        )
        project_page.link_projects_modal.click_on_button('Done')
        utils.wait_until_page_ready(driver)
        # Verify that project is linked
        project_page.scroll_into_view(project_page.linked_projects_section.element)
        utils.wait_until_page_ready(driver)
        linked_project_list = project_page.get_linked_project_list()
        assert link_project_title in linked_project_list
        project_page.remove_button.click()
        project_page.click_on_button('Delete')
        utils.wait_until_page_ready(driver)
        # Verify project link is removed
        project_page.scroll_into_view(project_page.linked_projects_section.element)
        linked_project_list = project_page.get_linked_project_list()
        assert link_project_title not in linked_project_list

    def test_remove_registration_link(self, driver, session, project_page):
        """This test verifies remove registration link from a
        project in overview page functionality."""

        link_registration_title = 'OSF Link Registration'
        project_page.scroll_into_view(project_page.linked_projects_section.element)
        project_page.click_on_button('Link Projects')
        project_page.link_projects_modal.click_on_button('Registrations')
        utils.wait_until_page_ready(driver)
        project_page.link_projects_modal.search_input.clear()
        project_page.link_projects_modal.search_input.send_keys(link_registration_title)
        project_page.link_projects_modal.select_project_checkbox_by_name(
            link_registration_title
        )
        project_page.link_projects_modal.click_on_button('Done')
        utils.wait_until_page_ready(driver)
        project_page.scroll_into_view(project_page.linked_projects_section.element)
        utils.wait_until_page_ready(driver)
        linked_project_list = project_page.get_linked_project_list()
        assert link_registration_title in linked_project_list
        project_page.remove_button.click()
        project_page.click_on_button('Delete')
        utils.wait_until_page_ready(driver)
        # Verify registration link is removed
        project_page.scroll_into_view(project_page.linked_projects_section.element)
        linked_project_list = project_page.get_linked_project_list()
        assert link_registration_title not in linked_project_list

    def test_project_overview(
        self, driver, session, project_details_page, default_project_with_all_metadata
    ):
        """This test verifies project details in overview page functionality."""

        node_id = default_project_with_all_metadata.id
        project_data = osf_api.get_node_details(session, node_id)
        api_description = project_data['attributes']['description']
        api_tags_list = project_data['attributes']['tags']
        api_created_date = project_data['attributes']['date_created']
        api_modified_date = project_data['attributes']['date_modified']

        api_project_license = osf_api.get_project_license_name(
            session=session, node_id=node_id
        )
        api_institution_list = osf_api.get_project_institutions(session, node_id)
        api_subjects = osf_api.get_project_subjects(session, node_id)
        api_authors = osf_api.get_project_contributors(session, node_id)

        # Retrieve registration details from UI
        assert ProjectPage(driver, verify=True)
        utils.wait_until_page_ready(driver)
        ui_description = project_details_page.overview_description.text.strip()
        ui_tags_list = project_details_page.get_tags_list()
        ui_created_date = project_details_page.overview_date_created.text.strip()
        ui_modified_date = project_details_page.overview_date_modified.text.strip()
        ui_license_info = project_details_page.overview_license.text.strip()
        ui_affiliated_institution_list = project_details_page.get_affiliations_list()
        ui_subjects_list = project_details_page.get_subjects_list()
        ui_authors_list = project_details_page.get_authors_list()

        # Verify that api data matches with UI data
        assert api_description == ui_description
        if settings.DOMAIN != 'stage3':
            assert utils.normalize_api_date(
                api_created_date
            ) == utils.normalize_ui_date(ui_created_date)
            assert utils.normalize_api_date(
                api_modified_date
            ) == utils.normalize_ui_date(ui_modified_date)

        if settings.DOMAIN != 'stage1':
            assert sorted(api_institution_list) == sorted(
                ui_affiliated_institution_list
            )

        assert sorted(api_tags_list) == sorted(ui_tags_list)
        assert api_project_license == ui_license_info
        assert sorted(api_subjects) == sorted(ui_subjects_list)

        for name, link in ui_authors_list:
            driver.get(link)
            profile_name = (
                WebDriverWait(driver, 10)
                .until(EC.visibility_of_element_located((By.XPATH, '//h1')))
                .text.strip()
            )
            assert name.replace(',', '') in api_authors
        assert name.replace(',', '') in profile_name

    def test_edit_metadata_button(
        self,
        driver,
        session,
        project_details_page_metadata,
        default_project_with_metadata,
        fake,
    ):
        """This test verifies edit project metadata button functionality in overview page navigates
        users to metadata page and user can edit metadata."""
        node_id = default_project_with_metadata.id
        assert ProjectPage(driver, verify=True)
        project_details_page_metadata.scroll_into_view(
            project_details_page_metadata.metadata_section.element
        )
        utils.wait_until_page_ready(driver)
        ui_description = project_details_page_metadata.overview_description.text.strip()
        project_details_page_metadata.edit_metadata_button.click()
        utils.wait_until_page_ready(driver)
        assert ProjectMetadataPage(driver, verify=True)
        metadata_page = ProjectMetadataPage(driver, guid=node_id)
        new_description = fake.sentence(nb_words=4)

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[h2[text()='Description']]//button[.='Edit']")
            )
        ).click()

        description_input = driver.find_element(By.ID, 'description')
        description_input.clear()
        description_input.send_keys(new_description)
        metadata_page.save_description_button.click()
        assert new_description == metadata_page.description.text.strip()
        # Verify on details page that description is edited
        details_page = ProjectPage(driver, guid=node_id)
        details_page.goto()
        utils.wait_until_page_ready(driver)
        details_page_description = details_page.overview_description.text.strip()
        assert ui_description != details_page_description
        assert details_page_description == new_description

    def test_view_only_links_button(
        self,
        driver,
        session,
        project_details_page_metadata,
        default_project_with_metadata,
    ):
        """This test verifies view_only_links button functionality in overview page navigates
        users to contributors page and user can create VOLs."""

        node_id = default_project_with_metadata.id
        assert ProjectPage(driver, verify=True)
        project_details_page_metadata.view_only_links_button.click()
        utils.wait_until_page_ready(driver)
        assert ContributorsPage(driver, verify=True)
        contributors_page = ContributorsPage(driver, guid=node_id)
        contributors_page.scroll_into_view(contributors_page.vol_section.element)
        contributors_page.click_on_button('Create')
        utils.wait_until_page_ready(driver)
        contributors_page.create_vol_modal.link_name_input.clear()
        contributors_page.create_vol_modal.link_name_input.send_keys('Selenium_VOL')
        contributors_page.create_vol_modal.click_on_button('Create')
        utils.wait_until_page_ready(driver)
        vol_name = contributors_page.link_name.text.strip()
        assert vol_name == 'Selenium_VOL'
        # Verify on details page that one VOL exists
        details_page = ProjectPage(driver, guid=node_id)
        details_page.goto()
        utils.wait_until_page_ready(driver)
        details_page.number_of_vols.text.strip() == 1
