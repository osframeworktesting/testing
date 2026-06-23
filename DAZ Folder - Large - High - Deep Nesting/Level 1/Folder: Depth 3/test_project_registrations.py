import time

import pytest
from selenium.webdriver.common.by import By

import markers
from api import osf_api
from pages.project import RegistrationsPage
from pages.registries import (
    DraftRegistrationMetadataPage,
    DraftRegistrationReviewPage,
)
from pages.support import SupportPage


@pytest.fixture()
def registrations_page(driver, default_project):
    """Fixture that uses a temporary project created in the testing environments and
    then navigates to the Registrations page for that project.
    """
    registrations_page = RegistrationsPage(driver, guid=default_project.id)
    registrations_page.goto()
    return registrations_page


@pytest.fixture()
def registrations_page_with_draft(driver, session, registrations_page):
    """This fixture uses the registrations_page fixture above and adds a draft
    registration to the temporary project.  NOTE: Since we are creating the draft
    registration from a temporary project that gets automatically deleted when we are
    done with it, the draft registration as a child of the project will also get
    deleted.
    """

    # First get the list of allowed registration schemas for OSF in a name and id pair
    # list. Then loop through the list to pull out just the id for the Open-Ended
    # Registration schema. We'll need this schema id to create the draft.
    schema_list = osf_api.get_registration_schemas_for_provider(provider_id='osf')
    for schema in schema_list:
        if schema[0] == 'Open-Ended Registration':
            schema_id = schema[1]
            break
    # Use the api to create a draft registration for the temporary project
    osf_api.create_draft_registration(
        session, node_id=registrations_page.guid, schema_id=schema_id
    )
    # Reload the page so that the draft is visible on the tab
    driver.find_element(By.ID, 'my-resources_header').click()
    time.sleep(1)
    driver.find_element(By.ID, 'my-registrations').click()
    time.sleep(1)
    registrations_page.draft_registrations_tab.click()
    return registrations_page


@markers.dont_run_on_prod
@pytest.mark.usefixtures('must_be_logged_in')
class TestProjectRegistrationsPage:
    def test_empty_registrations_tab(self, driver, registrations_page):
        """Tests that when the Project Registration page is first loaded, the submitted
        Registrations tab is selected and displayed by default. Also since this is a
        newly created project there should not be any existing submitted registrations.
        """
        assert driver.find_element(By.CSS_SELECTOR, 'p.ng-star-inserted').is_displayed()
        assert (
            driver.find_element(By.CSS_SELECTOR, 'p.ng-star-inserted').text
            == 'There have been no completed registrations of this project.'
        )

        assert registrations_page.registration_card.absent()
        assert driver.find_element(
            By.CSS_SELECTOR, 'button.p-button span.p-button-label'
        ).is_displayed()

    def test_create_new_registration_modal(self, driver, registrations_page):
        """Tests the Create Registration Page that opens when you click the
        New registration button on the Project Registrations page.
        """
        registrations_page.new_registration_button.click()
        create_registration_modal = registrations_page.create_registration_modal
        assert create_registration_modal.new_registration_page_title.present()
        assert driver.find_element(
            By.XPATH, "//h2[normalize-space(text())='Step 1']"
        ).is_displayed()
        driver.execute_script(
            'arguments[0].scrollIntoView(true);',
            driver.find_element(By.XPATH, "//button[.//span[text()='Create draft']]"),
        )
        time.sleep(1)
        assert create_registration_modal.create_draft_button.present()

        # Verify that the first schema in the list is pre-selected

        assert driver.find_element(
            By.XPATH, "//h2[normalize-space(text())='Step 2']"
        ).is_displayed()
        assert driver.find_element(
            By.XPATH, "//h2[normalize-space(text())='Step 3']"
        ).is_displayed()
        # Click 'here' link and verify redirection to support page
        driver.execute_script(
            'arguments[0].scrollIntoView(true);',
            driver.find_element(By.XPATH, "//a[normalize-space(text())='Click here']"),
        )
        registrations_page.here_support_link.click()
        assert SupportPage(driver, verify=True)

    def test_create_new_draft_registration(self, driver, registrations_page):
        """Tests the creation of a new draft registration from the Project Registrations
        page by clicking the New registration button on the page.  Then on the Create
        Registration modal window, select a schema and click the Create draft button to
        actually create the draft registration.
        """
        registrations_page.new_registration_button.click()
        create_registration_modal = registrations_page.create_registration_modal
        time.sleep(1)
        driver.execute_script(
            'arguments[0].scrollIntoView(true);',
            driver.find_element(By.XPATH, "//button[.//span[text()='Create draft']]"),
        )
        time.sleep(1)
        assert create_registration_modal.create_draft_button.present()
        create_registration_modal.create_draft_button.click()
        # Verify that you are redirected to the Draft Registration Metadata page
        DraftRegistrationMetadataPage(driver, verify=True)

    def test_review_draft_registration(
        self, session, driver, registrations_page_with_draft
    ):
        """Using the registrations_page_with_draft fixture that already has a draft
        registration created for the temporary project, verify that the draft
        registration is visible on the Draft registrations tab of the Project
        Registrations page.  Then click the Review button and verify that you are
        redirected to the Draft Registration Review page.
        """
        assert registrations_page_with_draft.draft_registration_card.present()
        assert driver.find_element(
            By.XPATH, "//h2[normalize-space(text())='OSF Test Project']"
        )
        assert driver.find_element(
            By.XPATH, "//span[normalize-space(text())='OSF Registries']"
        ).is_displayed()

        registrations_page_with_draft.review_draft_button.click()
        assert DraftRegistrationReviewPage(driver, verify=True)

    def test_edit_draft_registration(
        self, session, driver, registrations_page_with_draft
    ):
        """Using the registrations_page_with_draft fixture that already has a draft
        registration created for the temporary project, verify that the draft
        registration is visible on the Draft registrations tab of the Project
        Registrations page.  Then click the Edit button and verify that you are
        redirected to the Draft Registration Metadata page.
        """
        assert registrations_page_with_draft.draft_registration_card.present()
        assert driver.find_element(
            By.XPATH, "//h2[normalize-space(text())='OSF Test Project']"
        )
        registrations_page_with_draft.edit_draft_button.click()
        DraftRegistrationMetadataPage(driver, verify=True)

    def test_delete_draft_registration(
        self, session, driver, registrations_page_with_draft
    ):
        """Using the registrations_page_with_draft fixture that already has a draft
        registration created for the temporary project, verify that the draft
        registration is visible on the Draft registrations tab of the Project
        Registrations page.  Then verify that you can delete the draft registration
        using the Delete button on the page.
        """
        assert registrations_page_with_draft.draft_registration_card.present()
        assert driver.find_element(
            By.XPATH, "//h2[normalize-space(text())='OSF Test Project']"
        )
        # Click the Delete button for the Draft Registration card and then click the
        # Cancel button on the Confirm Delete Draft Registration Modal and verify the
        # Draft Registration card is still present.
        registrations_page_with_draft.delete_draft_button.click()
        registrations_page_with_draft.delete_draft_registration_modal.cancel_button.click()
        assert registrations_page_with_draft.draft_registration_card.present()
        # Now click the Delete button for the Draft Registration card again and this
        # time click the Delete button on the Confirm Delete Draft Registration Modal.
        # Then verify that the Draft Registration is no longer visible on the Draft
        # Registrations tab.
        registrations_page_with_draft.delete_draft_button.click()
        time.sleep(1)
        registrations_page_with_draft.delete_draft_registration_modal.delete_button.click()
        time.sleep(1)
        assert registrations_page_with_draft.draft_registration_card.absent()
        assert driver.find_element(
            By.XPATH, "//div[contains(text(), \"You don't have any registrations.\")]"
        ).is_displayed()
