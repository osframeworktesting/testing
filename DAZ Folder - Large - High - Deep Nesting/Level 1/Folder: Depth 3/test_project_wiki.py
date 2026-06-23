import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import markers
import utils
from pages.project import ProjectWikiPage


@markers.dont_run_on_prod
@pytest.mark.usefixtures('must_be_logged_in')
class TestProjectWiki:
    @pytest.fixture()
    def project_wiki_page(self, driver, default_project):
        project_wiki_page = ProjectWikiPage(driver, guid=default_project.id)
        project_wiki_page.goto()
        return project_wiki_page

    def test_edit_wiki_home(self, driver, session, project_wiki_page):
        """This test verifies editing wiki home page for a project."""

        wiki_text = 'Selenium Testing - Edit Wiki Home Page'
        project_wiki_page.click_on_button('Edit')
        project_wiki_page.wiki_edit_text.clear()
        project_wiki_page.wiki_edit_text.send_keys(wiki_text)
        project_wiki_page.click_on_button('Save')
        utils.wait_until_page_ready(driver)

        # Verify in preview that wiki is updated
        assert project_wiki_page.wiki_preview_text.text.strip() == wiki_text

    def test_revert_edit_wiki_home(self, driver, session, project_wiki_page):
        """This test verifies revreting back to original text in wiki home page for a project."""

        original_text = 'Selenium Testing - Edit Wiki Home Page'
        project_wiki_page.click_on_button('Edit')
        project_wiki_page.wiki_edit_text.clear()
        project_wiki_page.wiki_edit_text.send_keys(original_text)
        project_wiki_page.click_on_button('Save')
        utils.wait_until_page_ready(driver)

        # Verify in preview that wiki is updated
        assert project_wiki_page.wiki_preview_text.text.strip() == original_text

        new_wiki_text = 'Selenium Testing - New version of wiki'
        project_wiki_page.wiki_edit_text.clear()
        project_wiki_page.wiki_edit_text.send_keys(new_wiki_text)
        project_wiki_page.click_on_button('Revert')
        utils.wait_until_page_ready(driver)
        assert project_wiki_page.wiki_preview_text.text.strip() != new_wiki_text
        assert project_wiki_page.wiki_preview_text.text.strip() == original_text

    def test_view_wiki_versions(self, driver, session, project_wiki_page):
        """This test verifies view wiki home page versions for a project."""

        original_text = 'Selenium Testing - Edit Wiki Home Page'
        project_wiki_page.click_on_button('Edit')
        project_wiki_page.wiki_edit_text.clear()
        project_wiki_page.wiki_edit_text.send_keys(original_text)
        project_wiki_page.click_on_button('Save')
        utils.wait_until_page_ready(driver)
        assert '(Current)' in project_wiki_page.wiki_version.text.strip()
        assert project_wiki_page.wiki_preview_text.text.strip() == original_text

        new_wiki_text = 'Selenium Testing - New version of wiki'
        project_wiki_page.wiki_edit_text.clear()
        project_wiki_page.wiki_edit_text.send_keys(new_wiki_text)
        project_wiki_page.click_on_button('Save')
        utils.wait_until_page_ready(driver)

        # Verify version is current and preview shows updated text
        assert '(Current)' in project_wiki_page.wiki_version.text.strip()
        assert project_wiki_page.wiki_preview_text.text.strip() == new_wiki_text

        # Verify selecting previous version
        project_wiki_page.select_version_from_dropdown('(2)')
        utils.wait_until_page_ready(driver)
        assert project_wiki_page.wiki_preview_text.text.strip() == original_text

    def test_compare_wiki_versions(self, driver, session, project_wiki_page):
        """This test verifies compare wiki home page versions for a project."""

        wiki_text = 'Selenium Testing - Edit Wiki Home Page'
        project_wiki_page.click_on_button('Edit')
        project_wiki_page.wiki_edit_text.clear()
        project_wiki_page.wiki_edit_text.send_keys(wiki_text)
        project_wiki_page.click_on_button('Save')
        utils.wait_until_page_ready(driver)

        project_wiki_page.click_on_button('Edit')
        project_wiki_page.click_on_button('View')
        project_wiki_page.click_on_button('Compare')
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//h2[text()="Compare"]'))
        )

        assert project_wiki_page.compare_preview_text.text.strip() == 'Live preview to:'
        assert project_wiki_page.wiki_preview_text.text.strip() == wiki_text
        assert project_wiki_page.compare_text.text.strip() == wiki_text

    def test_add_new_wiki_page(self, driver, session, project_wiki_page):
        """This test verifies adding new wiki page for a project."""

        new_wiki_name = 'AQA Wiki Page'
        project_wiki_page.click_on_button('Add new wiki page')
        utils.wait_until_page_ready(driver)
        project_wiki_page.add_new_wiki_modal.wiki_name_input.clear()
        project_wiki_page.add_new_wiki_modal.wiki_name_input.send_keys(new_wiki_name)
        project_wiki_page.add_new_wiki_modal.click_on_button('Add')
        utils.wait_until_page_ready(driver)

        # Verify new page is in the pages list
        wiki_pages = project_wiki_page.get_wiki_pages()
        assert new_wiki_name in wiki_pages

    def test_rename_new_wiki_page(self, driver, session, project_wiki_page):
        """This test verifies renaming newly added wiki page for a project."""

        wiki_name = 'AQA Wiki Page'
        project_wiki_page.click_on_button('Add new wiki page')
        utils.wait_until_page_ready(driver)
        project_wiki_page.add_new_wiki_modal.wiki_name_input.clear()
        project_wiki_page.add_new_wiki_modal.wiki_name_input.send_keys(wiki_name)
        project_wiki_page.add_new_wiki_modal.click_on_button('Add')
        utils.wait_until_page_ready(driver)

        # Verify new page is in the pages list
        wiki_pages = project_wiki_page.get_wiki_pages()
        assert wiki_name in wiki_pages

        new_wiki_name = 'Selenium Edit - AQA Wiki Page'
        project_wiki_page.wiki_page_edit_button.click()
        utils.wait_until_page_ready(driver)
        project_wiki_page.edit_new_wiki_modal.wiki_name_input.clear()
        project_wiki_page.edit_new_wiki_modal.wiki_name_input.send_keys(new_wiki_name)
        project_wiki_page.edit_new_wiki_modal.click_on_button('Rename')
        utils.wait_until_page_ready(driver)
        # Verify old page is not available wiki pages list
        wiki_pages = project_wiki_page.get_wiki_pages()
        assert wiki_name not in wiki_pages
        # Verify new name is available in wiki pages list
        assert new_wiki_name in wiki_pages

    def test_cancel_rename_new_wiki_page(self, driver, session, project_wiki_page):
        """This test verifies renaming newly added wiki page for a project."""

        wiki_name = 'AQA Wiki Page'
        project_wiki_page.click_on_button('Add new wiki page')
        utils.wait_until_page_ready(driver)
        project_wiki_page.add_new_wiki_modal.wiki_name_input.clear()
        project_wiki_page.add_new_wiki_modal.wiki_name_input.send_keys(wiki_name)
        project_wiki_page.add_new_wiki_modal.click_on_button('Add')
        utils.wait_until_page_ready(driver)

        # Verify new page is in the pages list
        wiki_pages = project_wiki_page.get_wiki_pages()
        assert wiki_name in wiki_pages

        new_wiki_name = 'Selenium Edit - AQA Wiki Page'
        project_wiki_page.wiki_page_edit_button.click()
        utils.wait_until_page_ready(driver)
        project_wiki_page.edit_new_wiki_modal.wiki_name_input.clear()
        project_wiki_page.edit_new_wiki_modal.wiki_name_input.send_keys(new_wiki_name)
        project_wiki_page.edit_new_wiki_modal.click_on_button('Cancel')
        utils.wait_until_page_ready(driver)
        # Verify old page is not available wiki pages list
        wiki_pages = project_wiki_page.get_wiki_pages()

        # Verify new name is available in wiki pages list
        assert new_wiki_name not in wiki_pages

    def test_delete_new_wiki_page(self, driver, session, project_wiki_page):
        """This test verifies deleting newly added wiki page for a project."""

        wiki_name = 'AQA Wiki Page'
        project_wiki_page.click_on_button('Add new wiki page')
        utils.wait_until_page_ready(driver)
        project_wiki_page.add_new_wiki_modal.wiki_name_input.clear()
        project_wiki_page.add_new_wiki_modal.wiki_name_input.send_keys(wiki_name)
        project_wiki_page.add_new_wiki_modal.click_on_button('Add')
        utils.wait_until_page_ready(driver)

        # Verify new page is in the pages list
        wiki_pages = project_wiki_page.get_wiki_pages()
        assert wiki_name in wiki_pages

        # Delete newly created page
        project_wiki_page.click_on_button('Delete')
        utils.wait_until_page_ready(driver)
        project_wiki_page.delete_new_wiki_modal.click_on_delete_button('Delete')
        utils.wait_until_page_ready(driver)
        wiki_pages = project_wiki_page.get_wiki_pages()
        assert wiki_name not in wiki_pages

    def test_cancel_delete_new_wiki_page(self, driver, session, project_wiki_page):
        """This test verifies deleting newly added wiki page for a project."""

        wiki_name = 'AQA Wiki Page'
        project_wiki_page.click_on_button('Add new wiki page')
        utils.wait_until_page_ready(driver)
        project_wiki_page.add_new_wiki_modal.wiki_name_input.clear()
        project_wiki_page.add_new_wiki_modal.wiki_name_input.send_keys(wiki_name)
        project_wiki_page.add_new_wiki_modal.click_on_button('Add')
        utils.wait_until_page_ready(driver)

        # Verify new page is in the pages list
        wiki_pages = project_wiki_page.get_wiki_pages()
        assert wiki_name in wiki_pages

        # Delete newly created page
        project_wiki_page.click_on_button('Delete')
        utils.wait_until_page_ready(driver)
        project_wiki_page.delete_new_wiki_modal.click_on_button('Cancel')
        utils.wait_until_page_ready(driver)
        wiki_pages = project_wiki_page.get_wiki_pages()
        assert wiki_name in wiki_pages
