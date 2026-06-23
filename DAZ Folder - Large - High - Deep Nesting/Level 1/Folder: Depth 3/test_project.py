import time
from urllib.parse import urljoin

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import markers
import settings
from api import osf_api
from pages.login import (
    LoginPage,
    login,
    logout,
)
from pages.project import (  # verify_log_entry,
    ForksPage,
    ProjectPage,
    RequestAccessPage,
)


@pytest.fixture()
def project_page(driver, default_project_page):
    default_project_page.goto()
    return default_project_page


@pytest.fixture()
def project_page_with_file(driver, project_with_file):
    project_page = ProjectPage(driver, guid=project_with_file.id)
    project_page.goto()
    return project_page


@pytest.mark.usefixtures('must_be_logged_in')
class TestProjectDetailPage:
    @markers.smoke_test
    @markers.core_functionality
    def test_change_title(self, session, driver, project_page, fake):

        new_title = fake.sentence(nb_words=4)
        # fix locator for project title
        orig_title = project_page.title.text
        assert orig_title != new_title
        # In some cases (especially with Chrome) the test steps are executed faster than the web page is
        # really ready for them.  In this particular case the test clicks the title of the project which
        # is supposed to then produce an input box in which you can change the title.  If the click is
        # performed before the page is ready, then there is no input box and the test fails.  So we need
        # to provide a little extra time.  We can do this by waiting on the log widget to load.

        project_page.settings_link.click()
        project_page.log_widget.loading_indicator.here_then_gone()
        project_page.title_input.click()
        project_page.title_input.clear()
        project_page.title_input.send_keys(new_title)
        project_page.title_edit_submit_button.click()
        # Click 'overview' button from sidebar menu

        project_page.overview_link.click()
        # Wait for the page to reload
        assert project_page.title.text.lower() == new_title.lower()

    # Below test should be clarified and fixed if needed
    @markers.smoke_test
    @markers.core_functionality
    def log_widget_loads(self, project_page):
        project_page.log_widget.loading_indicator.here_then_gone()
        assert project_page.log_widget.log_items

    @markers.dont_run_on_prod
    @markers.dont_run_on_preferred_node
    @markers.core_functionality
    def test_make_public(self, session, driver, project_page):

        wait = WebDriverWait(driver, 5)

        # Set project to public
        project_page.public_project_switcher.click()
        wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, '//span[contains(text(), "Make Public")]')
            )
        )

        # First click the Cancel link on the Confirm Modal and verify that the project
        # is still private.
        project_page.confirm_privacy_change_modal.cancel_link.click()
        assert project_page.make_private_link.absent()

        # Click the Make Public link again and this time click the Confirm link on the
        # modal to actually make the project public.
        project_page.public_project_switcher.click()
        project_page.make_public_link.click()
        assert project_page.inactive_private_project.is_displayed()

        # Confirm logged out user can now see project
        logout(driver)
        project_page.goto()
        assert ProjectPage(driver, verify=True)
        login(driver)


@pytest.mark.usefixtures('must_be_logged_in_as_user_two')
class TestProjectDetailAsNonContributor:
    @markers.smoke_test
    @markers.core_functionality
    def test_is_private(self, driver, default_project_page):
        # Verify that a non contributor on a private project gets the request access page
        default_project_page.goto(expect_redirect_to=RequestAccessPage)


class TestProjectDetailLoggedOut:
    @markers.smoke_test
    @markers.core_functionality
    def test_is_private(self, driver, default_project_page):
        # Verify that a logged out user cannot see the project
        default_project_page.goto(expect_redirect_to=LoginPage)


class TestForksPage:
    @pytest.fixture()
    def forks_page(self, driver, default_project):
        forks_page = ForksPage(driver, guid=default_project.id)
        forks_page.goto()
        return forks_page

    @markers.dont_run_on_prod
    @markers.core_functionality
    def test_create_duplicate(
        self, driver, session, must_be_logged_in, forks_page, project_page
    ):
        wait = WebDriverWait(driver, 20)
        # In new version https://staging4.osf.io/encg6/analytics/duplicates
        forks_page.placeholder_text.present()
        assert len(forks_page.listed_forks) == 0
        # project_page.project_analytics_link.click()
        wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "[aria-label='Duplicate']")
            )
        ).click()
        time.sleep(2)
        forks_page.view_duplicates_button.click()
        time.sleep(2)
        forks_page.duplicate_project_button.click()

        forks_page.duplicate_project_modal_button.click()
        wait.until(
            EC.invisibility_of_element_located((By.XPATH, "//span[text()='Duplicate']"))
        )
        # time.sleep(5)
        # forks_page.reload()
        forks_page.verify()
        forks_page.fork_authors.present()
        assert len(forks_page.listed_forks) == 1

        orig_title = forks_page.project_title.text

        # Click the Title link on the Fork Card to navigate to the new Forked Project
        forks_page.view_duplicate.click()
        time.sleep(3)
        # Save ID of the duplicate
        current_url = driver.current_url
        fork_guid = current_url.rstrip('/').split('/')[-1]

        # forks_page.fork_link.click()
        assert ProjectPage(driver, verify=True)

        # THIS TEST IS NOT COMPLETED!!! Should be added logic after fixing an issue with displaying content of the duplicate
        fork_title = driver.find_element(
            By.XPATH, '//h1[contains(normalize-space(.), "Fork of")]'
        )
        assert fork_title.is_displayed()
        assert orig_title == fork_title.text

        # Clean-up leftover fork
        osf_api.delete_project(session, fork_guid, None)


@markers.dont_run_on_prod
@pytest.mark.usefixtures('must_be_logged_in')
class TestProjectComponents:
    def test_add_component(self, driver, session, project_page):
        """Test the functionality of adding a new child component node to a project"""

        # Click Add Component button and on the Create Component Modal, first click the
        # Cancel button and verify that there are no components listed on the Project
        # Overview page.

        # driver.find_element(By.CSS_SELECTOR, "button.p-button span.p").click()
        project_page.loading_indicator.here_then_gone()
        project_page.add_component_button.click()
        time.sleep(2)
        # project_page.create_component_modal.cancel_button.click()
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, "//span[text()='Cancel']"))
        ).click()
        WebDriverWait(driver, 3).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, 'div.modal-backdrop.fade')
            )
        )
        assert len(project_page.components) == 0

        # Click the Add Component button again and this time enter data on the modal to
        # add a new component
        project_page.add_component_button.click()
        time.sleep(2)
        project_page.component_title_input.click()
        project_page.component_title_input.clear()
        project_page.component_title_input.send_keys_deliberately('Selenium Component')
        project_page.component_description_input.click()
        project_page.component_description_input.send_keys_deliberately(
            'This component was added by an automated selenium test.'
        )

        project_page.create_component_button.click()
        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located((By.XPATH, "//span[text()='Create']"))
        )

        # Get the guid for the component from the Go to new component link on the
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'a.component-title'))
        ).click()
        # Component Created Confirmation modal
        time.sleep(2)
        current_url = driver.current_url
        component_guid = current_url.rstrip('/').split('/')[-2]

        try:
            # Click the Go to new component link and verify that you are navigated to
            # the Overview page of a new node

            component_page = ProjectPage(driver, verify=True)
            assert component_page.title.text == 'Selenium Component'
            assert (
                driver.find_element_by_xpath(
                    '//div[text()="This component was added by an automated selenium test."]'
                ).text
                == 'This component was added by an automated selenium test.'
            )

            component_page.scroll_into_view(component_page.parent_project_link.element)
            component_page.parent_project_link.click()
            assert project_page

        finally:
            # The parent project should be automatically deleted by the fixture code.
            # But it cannot be deleted if the component is not deleted first.
            osf_api.delete_project(session, component_guid, None)

    def test_delete_component_from_project(self, driver, session, default_project):
        """Test the functionality of deleting a child component node from the parent
        project's Project Overview page.
        """

        # First use the api to create a child node for the dummy temporary project
        component = osf_api.create_child_node(
            session, node=default_project, title='API Created Component'
        )

        try:
            # Navigate to the parent Project Overview page and verify the existence of
            # the component
            project_page = ProjectPage(driver, guid=default_project.id)
            project_page.goto()
            assert ProjectPage(driver, verify=True)
            assert driver.find_element(
                By.XPATH, "//a[normalize-space(text())='API Created Component']"
            ).is_displayed()

            # Click the button on the right side of the component card to reveal a
            # dropdown options menu
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//button[.//span[contains(@class,'fa-ellipsis-vertical')]]",
                    )
                )
            ).click()

            # Click the Delete menu option
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.XPATH, "//a[text()=' Delete ']"))
            ).click()

            # On the Delete Component Confirmation Modal, first verify that the Delete
            # button is disabled. Then click the Cancel button to go back to the Project
            # Overview page again and verify the component card is still there.
            assert (
                WebDriverWait(driver, 5)
                .until(
                    EC.visibility_of_element_located(
                        (By.XPATH, "//span[text()='Delete']")
                    )
                )
                .is_displayed()
            )
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.XPATH, "//span[text()='Cancel']"))
            ).click()

            # Select the Component Delete menu option again and this time enter the
            # confirmation text value in the input field and click the Delete button to
            # actually delete the component.
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//button[.//span[contains(@class,'fa-ellipsis-vertical')]]",
                    )
                )
            ).click()

            # Click the Delete menu option
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//a[normalize-space(text())="Delete"]')
                )
            ).click()
            # time.sleep(2)
            confirmation_word_value = (
                WebDriverWait(driver, 5)
                .until(EC.visibility_of_element_located((By.XPATH, '//p/strong')))
                .text
            )

            # Send confirmation_word_value to input field
            driver.find_element(By.CSS_SELECTOR, 'input.p-inputtext').send_keys(
                confirmation_word_value
            )
            project_page.delete_component_modal_button.click()

            # Verify that back on the Project Overview page an alert message appears at
            # the top of the page indicating that the component was deleted and the
            # Component section no longer has the card for the deleted component.

            assert (
                WebDriverWait(driver, 5)
                .until(
                    EC.visibility_of_element_located(
                        (
                            By.XPATH,
                            "//div[text()='Component has been deleted successfully']",
                        )
                    )
                )
                .is_displayed()
            )
            assert (
                WebDriverWait(driver, 5)
                .until(
                    EC.visibility_of_element_located(
                        (
                            By.XPATH,
                            "//em[contains(text(), 'Add components to organize your project.')]",
                        )
                    )
                )
                .is_displayed()
            )

            assert len(project_page.components) == 0

        finally:
            # We must make sure that in the event of an error that we delete the
            # component so that the dummy project can also be deleted.
            if osf_api.get_node(session, node_id=component.id):
                osf_api.delete_project(session, component.id, None)

    def test_make_public_project_with_component(self, driver, session, default_project):
        """Test the functionality of making Public a project that has a child component
        node.
        """

        # First use the api to create a child node for the dummy temporary project
        component = osf_api.create_child_node(
            session, node=default_project, title='API Created Component'
        )

        try:
            # Navigate to the parent Project Overview page and verify the existence of
            # the component
            project_page = ProjectPage(driver, guid=default_project.id)
            project_page.goto()
            assert ProjectPage(driver, verify=True)

            # Click the Make Public link at the top of the page and then click the
            # Continue link on the first confirmation modal.
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, '[data-pc-name="toggleswitch"]')
                )
            ).click()
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//button[.//span[normalize-space()='Continue']]")
                )
            ).click()
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//button[.//span[normalize-space()='Confirm']]")
                )
            ).click()
            assert project_page.inactive_private_project.is_displayed()

            # Verify logged out user can now see project
            logout(driver)
            project_page.goto()
            assert ProjectPage(driver, verify=True)

            # Also navigate to Component and verify logged out user can see it as well
            component_page = ProjectPage(driver, guid=component.id)
            component_page.goto()
            assert ProjectPage(driver, verify=True)
        finally:
            # We must make sure that in the event of an error that we delete the
            # component so that the dummy project can also be deleted.
            if osf_api.get_node(session, node_id=component.id):
                osf_api.delete_project(session, component.id, None)


@markers.dont_run_on_prod
@pytest.mark.usefixtures('hide_footer_slide_in')
class TestProjectVOLs:
    def test_vol_project_overview_page(self, driver, session, project_with_file):
        """Test that creates a View Only Link using the OSF api and then uses that VOL
        to navigate to the Project Overview page for the project.
        """

        vol_key = osf_api.create_project_view_only_link(session, project_with_file.id)
        # Create the VOL URL for the Project and use the link to navigate to the Project
        # Overview page
        url_addition = '{}/?view_only={}'.format(project_with_file.id, vol_key)
        vol_url = urljoin(settings.OSF_HOME, url_addition)
        driver.get(vol_url)
        project_page = ProjectPage(driver, verify=True)
        project_page.loading_indicator.here_then_gone()

        # Verify that we are not logged in

        # Verify VOL message at the top of the page
        assert driver.find_element(
            By.XPATH,
            "//p[text()=' You are viewing OSF through a view-only link, which may limit the data you have permission to see. ']",
        ).is_displayed()

        # Verify Contributor is visible
        user = osf_api.current_user()
        assert project_page.contributors_list.text == user.full_name

        # Verify File Widget loads
        assert project_page.file_widget.first_file

    def test_avol_project_overview_page(self, driver, session, project_with_file):
        """Test that creates an Anonymous View Only Link using the OSF api and then uses
        that AVOL to navigate to the Project Overview page for the project.
        """

        avol_key = osf_api.create_project_view_only_link(
            session, project_with_file.id, anonymous=True
        )
        # Create the AVOL URL for the Project and use the link to navigate to the Project
        # Overview page
        url_addition = '{}/?view_only={}'.format(project_with_file.id, avol_key)
        avol_url = urljoin(settings.OSF_HOME, url_addition)
        driver.get(avol_url)
        project_page = ProjectPage(driver, verify=True)
        project_page.loading_indicator.here_then_gone()

        # Verify VOL message at the top of the page
        assert driver.find_element(
            By.XPATH,
            "//p[text()=' You are viewing OSF through a view-only link, which may limit the data you have permission to see. ']",
        ).is_displayed()

        # Verify Contributor is NOT visible

        assert (
            driver.find_element(
                By.XPATH, '//div[@class="flex flex-wrap gap-1 line-height-2"]'
            ).text
            == 'Anonymous Contributors'
        )

        # Verify File Widget loads
        assert project_page.file_widget.first_file
