import time

import pytest
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

import markers
from pages.cos import COSDonatePage
from pages.dashboard import DashboardPage
from pages.institutions import InstitutionsLandingPage
from pages.landing import LandingPage
from pages.login import (
    LoginPage,
    accept_cookies,
)
from pages.meetings import MeetingsPage
from pages.preprints import (
    NewPreprintsProviderServicePage,
    PreprintLandingPage,
    ReviewsDashboardPage,
)
from pages.project import (
    MyProjectsPage,
    ProjectPage,
)
from pages.registrations import MyRegistrationsPage
from pages.registries import RegistriesLandingPage
from pages.search import SearchPage
from pages.support import SupportPage
from pages.user import (
    ProfileInformationPage,
    UserProfilePage,
)


class NavbarTestLoggedOutMixin:
    """Mixin used to inject generic tests"""

    @pytest.fixture()
    def page(self, driver):
        raise NotImplementedError()

    def test_osf_home_dropdown_link(self, page, driver):
        accept_cookies(driver)
        page.navbar.home_link.click()
        LandingPage(driver, verify=True)

    def test_preprints_dropdown_link(self, page, driver):
        page.navbar.preprints_link.click()
        PreprintLandingPage(driver, verify=True)

    def test_registries_dropdown_link(self, driver, page):
        page.navbar.registries_link.click()
        RegistriesLandingPage(driver, verify=True)

    def test_meetings_dropdown_link(self, page, driver):
        page.navbar.meetings_link.click()
        MeetingsPage(driver, verify=True)

    def test_institutions_dropdown_link(self, page, driver):
        page.navbar.institutions_link.click()
        InstitutionsLandingPage(driver, verify=True)

    def test_donate_link(self, page, driver):
        accept_cookies(driver)
        page.navbar.donate_link.click()
        COSDonatePage(driver, verify=True)

    def test_sign_in_button(self, page, driver):
        accept_cookies(driver)
        page.navbar.sign_in_button.click()
        LoginPage(driver, verify=True)

    def test_user_dropdown_not_present(self, page):
        assert page.navbar.user_dropdown.absent()


class NavbarTestLoggedInMixin:
    """Mixin used to inject generic tests"""

    @pytest.fixture()
    def page(self, driver):
        raise NotImplementedError()

    def test_user_profile_menu_profile_link(self, driver, page):
        page.navbar.user_profile_link.click()
        assert UserProfilePage(driver, verify=True)

    def test_user_profile_menu_settings_link(self, driver, page):
        driver.execute_script(
            'arguments[0].scrollIntoView(true);',
            driver.find_element(By.ID, 'settings_header'),
        )
        driver.find_element(By.ID, 'my-profile_header').click()
        time.sleep(1)
        assert ProfileInformationPage(driver, verify=True)

    def test_sign_in_button_not_present(self, page):
        assert page.navbar.sign_in_button.absent()

    def test_sign_up_button_not_present(self, page):
        assert page.navbar.sign_up_button.absent()

    def test_logout_link(self, driver, page):
        # page.navbar.user_dropdown.click()
        page.scroll_into_view(driver.find_element(By.ID, 'log-out_header'))
        time.sleep(2)
        page.navbar.logout_link.click()
        LandingPage(driver, verify=True)


@markers.smoke_test
@markers.core_functionality
@pytest.mark.usefixtures('throttle_on_prod')
class TestOSFHomeNavbarLoggedOut(NavbarTestLoggedOutMixin):
    @pytest.fixture()
    def page(self, driver):
        page = LandingPage(driver)
        page.goto_with_reload()
        return page

    def test_my_projects_link_not_present(self, driver, page):
        try:
            driver.find_element(By.ID, 'my-projects')
            assert False
        except NoSuchElementException:
            pass

    def test_search_link(self, driver, page):
        accept_cookies(driver)
        page.navbar.search_link.click()
        assert SearchPage(driver, verify=True)

    def test_support_link(self, page, driver):
        accept_cookies(driver)
        time.sleep(1)
        page.navbar.support_link.click()
        assert SupportPage(driver, verify=True)


@markers.smoke_test
@markers.core_functionality
@pytest.mark.usefixtures('throttle_on_prod')
class TestOSFHomeNavbarLoggedIn(NavbarTestLoggedInMixin):
    @pytest.fixture()
    def page(self, driver, log_in_if_not_already):
        page = DashboardPage(driver)
        page.goto_with_reload()
        return page

    def test_my_projects_link(self, page, driver):
        page.navbar.my_osf_link.click()
        time.sleep(1)
        page.navbar.my_projects_link.click()
        assert MyProjectsPage(driver, verify=True)


@markers.smoke_test
@markers.core_functionality
@pytest.mark.usefixtures('log_in_if_not_already')
@pytest.mark.usefixtures('throttle_on_prod')
class TestPreprintsNavbarLoggedIn(NavbarTestLoggedInMixin):
    @pytest.fixture()
    def page(self, driver):
        page = PreprintLandingPage(driver)
        page.goto_with_reload()
        return page

    def test_add_a_preprint_link(self, page, driver):

        page.navbar.add_a_preprint_link.click()
        NewPreprintsProviderServicePage(driver, verify=True)

    def test_my_preprints_link(self, page, driver):
        page.navbar.my_osf_link.click()
        time.sleep(1)
        page.navbar.my_preprints_link.click()
        time.sleep(3)
        # My Preprints link actually navigates to My Preprints section of My Projects page
        assert '/my-preprints' in driver.current_url

    # In order to see the My Reviewing link in the Preprints Navbar the user has to be
    # an admin for one of the Branded Preprint Providers.
    @markers.dont_run_on_prod
    def my_reviewing_link(self, page, driver):
        page.navbar.my_reviewing_link.click()
        ReviewsDashboardPage(driver, verify=True)


@markers.smoke_test
@markers.core_functionality
@pytest.mark.usefixtures('throttle_on_prod')
class TestRegistriesNavbarLoggedOut(NavbarTestLoggedOutMixin):
    @pytest.fixture()
    def page(self, driver):
        page = RegistriesLandingPage(driver)
        page.goto_with_reload()
        return page

    # In the Registries navbar there is no Sign In button, instead it is a Login link
    def test_sign_in_button(self, page, driver):
        page.navbar.login_link.click()
        LoginPage(driver, verify=True)


@markers.smoke_test
@markers.core_functionality
@pytest.mark.usefixtures('log_in_if_not_already')
@pytest.mark.usefixtures('throttle_on_prod')
class TestRegistriesNavbarLoggedIn(NavbarTestLoggedInMixin):
    @pytest.fixture()
    def page(self, driver):
        page = RegistriesLandingPage(driver)
        page.goto_with_reload()
        return page

    def test_my_registrations_link(self, page, driver):
        page.navbar.my_osf_link.click()
        time.sleep(1)
        page.navbar.my_registrations_link.click()
        MyRegistrationsPage(driver, verify=True)


@markers.smoke_test
@markers.core_functionality
@pytest.mark.usefixtures('log_in_if_not_already')
@pytest.mark.usefixtures('throttle_on_prod')
class TestMeetingsNavbarLoggedIn(NavbarTestLoggedInMixin):
    @pytest.fixture()
    def page(self, driver):
        page = MeetingsPage(driver)
        page.goto_with_reload()
        return page


@markers.smoke_test
@markers.core_functionality
@pytest.mark.usefixtures('log_in_if_not_already')
@pytest.mark.usefixtures('throttle_on_prod')
class TestInstitutionsNavbarLoggedIn(NavbarTestLoggedInMixin):
    @pytest.fixture()
    def page(self, driver):
        page = InstitutionsLandingPage(driver)
        page.goto_with_reload()
        return page


def assert_donate_page(driver, donate_page):
    # locators.py does not currently support invisible elements as identity
    # https://github.com/cos-qa/osf-selenium-tests/blob/b7f3f21376b7d6f751993cdcffea9262856263e3/base/locators.py#L138
    # meta_tag = driver.find_element_by_xpath(
    #     '//meta[@property="og:title" and contains(@content, "Support COS")]'
    # )

    assert 'support-cos' in driver.current_url


@markers.smoke_test
@markers.core_functionality
@pytest.mark.usefixtures('log_in_if_not_already')
@pytest.mark.usefixtures('throttle_on_prod')
class TestProjectsNavbarLoggedIn:
    @pytest.fixture()
    def project_page(self, driver, default_project_page):
        default_project_page.goto()
        return default_project_page

    @pytest.fixture()
    def page(self, driver, project_with_file):
        page = ProjectPage(driver, guid=project_with_file.id)
        page.goto()
        return page

    def test_search_link(self, session, driver, page):
        page.navbar.search_link.click()
        SearchPage(driver, verify=True)

    def test_support_link(self, session, driver, page):
        page.navbar.support_link.click()
        SupportPage(driver, verify=True)

    def test_donate_link(self, session, driver, page):
        driver.execute_script(
            'arguments[0].scrollIntoView(true);',
            driver.find_element(By.ID, 'donate_header'),
        )
        time.sleep(1)
        page.navbar.donate_link.click()
        tabs = driver.window_handles
        driver.switch_to.window(tabs[1])
        time.sleep(2)
        donate_page = COSDonatePage(driver, verify=False)
        assert_donate_page(driver, donate_page)
