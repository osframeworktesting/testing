import pytest

import markers
import utils
from api import osf_api
from pages.registries import (
    ModeratorDashboardPage,
    ModeratorSettingsPage,
)
from pages.user import SettingsNotificationsPage


def verify_title_sorting(titles, ascending=True):
    """
    Verify titles are sorted across all pages.
    """
    expected = sorted(titles, key=lambda x: x.lower(), reverse=not ascending)

    assert titles == expected, (
        f'Title sorting failed.\n' f'Actual: {titles}\n' f'Expected: {expected}'
    )


@pytest.mark.usefixtures('must_be_logged_in_as_admin_user')
@markers.dont_run_on_prod
@markers.core_functionality
class TestRegistrationModeration:
    def test_add_moderator(self, session, driver):
        """Test to verify add moderator to a branded registration provider"""
        moderator_user = 'OSF Runscope Write'
        user_id = osf_api.get_user_guid(session, moderator_user)
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to moderator tab
        moderator_dashboard_page.select_tab('Moderators')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.click_on_button('Add moderator')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.add_moderator_modal.search_input.clear()
        moderator_dashboard_page.add_moderator_modal.search_input.send_keys(
            moderator_user
        )
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.add_moderator_modal.select_user_checkbox(user_id)
        moderator_dashboard_page.add_moderator_modal.click_on_button('Add')
        utils.wait_until_page_ready(driver)

        # Verify that user is added successfully and available in the list
        moderator_dashboard_page.search_input.clear()
        moderator_dashboard_page.search_input.send_keys(moderator_user)
        utils.wait_until_page_ready(driver)
        assert moderator_dashboard_page.user_name.text.strip() == moderator_user

    def test_edit_moderator_permission(self, session, driver):
        """Test to verify edit moderator permission for a branded registration provider"""
        moderator_user = 'OSF Runscope Write'
        moderator_permission = 'Administrator'
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to moderator tab
        moderator_dashboard_page.select_tab('Moderators')
        utils.wait_until_page_ready(driver)

        moderator_dashboard_page.search_input.clear()
        moderator_dashboard_page.search_input.send_keys(moderator_user)
        utils.wait_until_page_ready(driver)
        original_moderator_permission = (
            moderator_dashboard_page.user_permission.text.strip()
        )
        moderator_dashboard_page.select_permission_from_dropdown_listbox(
            moderator_permission
        )
        utils.wait_until_page_ready(driver)
        new_moderator_permission = moderator_dashboard_page.user_permission.text.strip()
        assert original_moderator_permission != new_moderator_permission
        assert moderator_permission == new_moderator_permission

    def test_remove_moderator(self, session, driver):
        """Test to verify removing moderator for a branded registration provider"""
        moderator_user = 'OSF Runscope Write'
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to moderator tab
        moderator_dashboard_page.select_tab('Moderators')
        utils.wait_until_page_ready(driver)

        moderator_dashboard_page.search_input.clear()
        moderator_dashboard_page.search_input.send_keys(moderator_user)
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.click_on_remove_moderator_icon()
        moderator_dashboard_page.remove_moderator_modal.click_on_button('Remove')
        utils.wait_until_page_ready(driver)
        # Verify user is not in the moderators list
        moderator_dashboard_page.search_input.clear()
        moderator_dashboard_page.search_input.send_keys(moderator_user)
        assert (
            moderator_dashboard_page.no_results_message.text.strip()
            == 'No results found.'
        )


@pytest.mark.usefixtures('must_be_logged_in')
@markers.dont_run_on_prod
@markers.core_functionality
class TestRegistrationModerationPendingTabSorting:
    def test_pending_tab_sort_name_a_to_z(self, driver, session):
        """Test to verify sorting pending registration submissions by title"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Pending')
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: A-Z')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles)
        else:
            print('No pending submissions were found.')

    def test_pending_tab_sort_name_z_to_a(self, driver, session):
        """Test to verify sorting pending registration submissions by title"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Pending')
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: Z-A')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles, ascending=False)
        else:
            print('No pending submissions were found.')

    def test_pending_tab_sort_date_newest_to_oldest(self, driver, session):
        """Test to verify sorting pending registration submissions by date"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Pending')
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: newest to oldest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates)
        else:
            print('No pending submissions were found.')

    def test_pending_tab_sort_date_oldest_to_newest(self, driver, session):
        """Test to verify sorting pending registration
        submissions by date."""
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Pending')
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: oldest to newest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates, reverse=True)
        else:
            print('No pending submissions were found.')

    def test_pending_updates_tab_sort_name_a_to_z(self, driver, session):
        """Test to verify sorting pending registration updates by title"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Pending')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.pending_updates_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: A-Z')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles)
        else:
            print('No pending updates were found.')

    def test_pending_updates_tab_sort_name_z_to_a(self, driver, session):
        """Test to verify sorting pending registration updates by title"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Pending')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.pending_updates_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: Z-A')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles, ascending=False)
        else:
            print('No pending updates were found.')

    def test_pending_updates_tab_sort_date_newest_to_oldest(self, driver, session):
        """Test to verify sorting pending registration updates by date"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Pending')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.pending_updates_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: newest to oldest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates)
        else:
            print('No pending updates were found.')

    def test_pending_updates_sort_date_oldest_to_newest(self, driver, session):
        """Test to verify sorting pending registration
        updates by date."""
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Pending')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.pending_updates_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: oldest to newest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates, reverse=True)
        else:
            print('No pending updates were found.')

    def test_pending_withdrawal_tab_sort_name_a_to_z(self, driver, session):
        """Test to verify sorting pending registration withdrawals by title"""
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Pending')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.pending_updates_button.click()
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.pending_withdrawal_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: A-Z')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles)
        else:
            print('No pending withdrawals were found.')

    def test_pending_withdrawal_tab_sort_name_z_to_a(self, driver, session):
        """Test to verify sorting pending registration withdrawals by title"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Pending')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.pending_withdrawal_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: Z-A')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles, ascending=False)
        else:
            print('No pending withdrawals were found.')

    def test_pending_withdrawal_tab_sort_date_newest_to_oldest(self, driver, session):
        """Test to verify sorting pending registration withdrawals by date"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Pending')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.pending_withdrawal_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: newest to oldest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates)
        else:
            print('No pending withdrawals were found.')

    def test_pending_withdrawal_sort_date_oldest_to_newest(self, driver, session):
        """Test to verify sorting pending registration
        withdrawals by date."""
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Pending')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.pending_withdrawal_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: oldest to newest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates, reverse=True)
        else:
            print('No pending withdrawals were found.')


@pytest.mark.usefixtures('must_be_logged_in')
@markers.dont_run_on_prod
@markers.core_functionality
class TestRegistrationModerationSubmittedTabSorting:
    def test_submitted_tab_sort_name_a_to_z(self, driver, session):
        """Test to verify sorting submitted public registrations by title"""
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: A-Z')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles)
        else:
            print('No public submissions were found.')

    def test_submitted_tab_sort_name_z_to_a(self, driver, session):
        """Test to verify sorting pending registration submissions by title"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: Z-A')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles, ascending=False)
        else:
            print('No public submissions were found.')

    def test_submitted_tab_sort_date_newest_to_oldest(self, driver, session):
        """Test to verify sorting pending registration submissions by date"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: newest to oldest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates)
        else:
            print('No public submissions were found.')

    def test_submitted_tab_sort_date_oldest_to_newest(self, driver, session):
        """Test to verify sorting pending registration
        submissions by date."""
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: oldest to newest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates, reverse=True)
        else:
            print('No public submissions were found.')

    def test_submitted_embargo_tab_sort_name_a_to_z(self, driver, session):
        """Test to verify sorting submitted public registrations by title"""
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.submitted_embargo_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: A-Z')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles)
        else:
            print('No embargoed submissions were found.')

    def test_submitted_embargo_tab_sort_name_z_to_a(self, driver, session):
        """Test to verify sorting pending registration submissions by title"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.submitted_embargo_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: Z-A')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles, ascending=False)
        else:
            print('No embargoed submissions were found.')

    def test_submitted_embargo_tab_sort_date_newest_to_oldest(self, driver, session):
        """Test to verify sorting pending registration submissions by date"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.submitted_embargo_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: newest to oldest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates)
        else:
            print('No embargoed submissions were found.')

    def test_submitted_embargo_tab_sort_date_oldest_to_newest(self, driver, session):
        """Test to verify sorting pending registration
        submissions by date."""
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.submitted_embargo_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: oldest to newest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates, reverse=True)
        else:
            print('No embargoed submissions were found.')

    def test_submitted_rejected_tab_sort_name_a_to_z(self, driver, session):
        """Test to verify sorting submitted public registrations by title"""
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.submitted_rejected_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: A-Z')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles)
        else:
            print('No rejected submissions were found.')

    def test_submitted_rejected_tab_sort_name_z_to_a(self, driver, session):
        """Test to verify sorting pending registration submissions by title"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.submitted_rejected_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: Z-A')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles, ascending=False)
        else:
            print('No rejected submissions were found.')

    def test_submitted_rejected_tab_sort_date_newest_to_oldest(self, driver, session):
        """Test to verify sorting pending registration submissions by date"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.submitted_rejected_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: newest to oldest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates)
        else:
            print('No rejected submissions were found.')

    def test_submitted_rejected_tab_sort_date_oldest_to_newest(self, driver, session):
        """Test to verify sorting pending registration
        submissions by date."""
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.submitted_rejected_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: oldest to newest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates, reverse=True)
        else:
            print('No rejected submissions were found.')

    def test_submitted_withdrawn_tab_sort_name_a_to_z(self, driver, session):
        """Test to verify sorting submitted public registrations by title"""
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.submitted_withdrawn_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: A-Z')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles)
        else:
            print('No withdrawn submissions were found.')

    def test_submitted_withdrawn_tab_sort_name_z_to_a(self, driver, session):
        """Test to verify sorting withdrawn registration submissions by title"""
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.submitted_withdrawn_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Title: Z-A')
            utils.wait_until_page_ready(driver)
            titles = moderator_dashboard_page.get_all_titles()
            verify_title_sorting(titles, ascending=False)
        else:
            print('No withdrawn submissions were found.')

    def test_submitted_withdrawn_tab_sort_date_newest_to_oldest(self, driver, session):
        """Test to verify sorting withdrawn registration submissions by date"""

        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.submitted_withdrawn_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: newest to oldest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates)
        else:
            print('No withdrawn submissions were found.')

    def test_submitted_withdrawn_tab_sort_date_oldest_to_newest(self, driver, session):
        """Test to verify sorting withdrawn registration
        submissions by date."""
        moderator_dashboard_page = ModeratorDashboardPage(driver)
        moderator_dashboard_page.goto_short()
        assert ModeratorDashboardPage(driver, verify=True)
        # Navigate to Pending tab
        moderator_dashboard_page.select_tab('Submitted')
        utils.wait_until_page_ready(driver)
        moderator_dashboard_page.submitted_withdrawn_button.click()
        utils.wait_until_page_ready(driver)
        default_selection = (
            moderator_dashboard_page.selected_sorting_option.text.strip()
        )
        assert default_selection == 'Date: newest to oldest'
        if moderator_dashboard_page.verify_results_exist():
            moderator_dashboard_page.select_sorting_option('Date: oldest to newest')
            utils.wait_until_page_ready(driver)
            all_dates = moderator_dashboard_page.get_all_dates()
            assert all_dates == sorted(all_dates, reverse=True)
        else:
            print('No withdrawn submissions were found.')


@markers.dont_run_on_prod
@markers.core_functionality
@pytest.mark.usefixtures('must_be_logged_in')
class TestRegistrationModeratorNotifications:
    def test_new_pending_submission_notification_daily(self, session, driver):
        """Test to verify registration new pending submission notifications settings
        for a given moderator."""
        moderator_settings_page = ModeratorSettingsPage(driver)
        moderator_settings_page.goto_short()
        assert ModeratorSettingsPage(driver, verify=True)
        initial_frequency = (
            moderator_settings_page.new_pending_submission_notification_freq.text.strip()
        )
        new_frequency = 'Daily'
        assert initial_frequency != new_frequency
        moderator_settings_page.select_from_pending_submissions_dropdown(new_frequency)
        utils.wait_until_page_ready(driver)
        assert (
            moderator_settings_page.new_pending_submission_notification_freq.text.strip()
            == new_frequency
        )

    def test_new_pending_submission_notification_never(self, session, driver):
        """Test to verify registration new pending submission notifications settings
        for a given moderator."""
        moderator_settings_page = ModeratorSettingsPage(driver)
        moderator_settings_page.goto_short()
        assert ModeratorSettingsPage(driver, verify=True)
        initial_frequency = (
            moderator_settings_page.new_pending_submission_notification_freq.text.strip()
        )
        new_frequency = 'Never'
        assert initial_frequency != new_frequency
        moderator_settings_page.select_from_pending_submissions_dropdown(new_frequency)
        utils.wait_until_page_ready(driver)
        assert (
            moderator_settings_page.new_pending_submission_notification_freq.text.strip()
            == new_frequency
        )

    def test_new_pending_submission_notification_instant(self, session, driver):
        """Test to verify registration new pending submission notifications settings
        for a given moderator."""
        moderator_settings_page = ModeratorSettingsPage(driver)
        moderator_settings_page.goto_short()
        assert ModeratorSettingsPage(driver, verify=True)
        initial_frequency = (
            moderator_settings_page.new_pending_submission_notification_freq.text.strip()
        )
        new_frequency = 'Instant'
        assert initial_frequency != new_frequency
        moderator_settings_page.select_from_pending_submissions_dropdown(new_frequency)
        utils.wait_until_page_ready(driver)
        assert (
            moderator_settings_page.new_pending_submission_notification_freq.text.strip()
            == new_frequency
        )

    def test_withdraw_requests_notification_daily(self, session, driver):
        """Test to verify registration new pending submission notifications settings
        for a given moderator."""
        moderator_settings_page = ModeratorSettingsPage(driver)
        moderator_settings_page.goto_short()
        assert ModeratorSettingsPage(driver, verify=True)
        initial_frequency = (
            moderator_settings_page.new_pending_withdraw_requests_notification_freq.text.strip()
        )
        new_frequency = 'Daily'
        assert initial_frequency != new_frequency
        moderator_settings_page.select_from_withdraw_requests_dropdown(new_frequency)
        utils.wait_until_page_ready(driver)
        assert (
            moderator_settings_page.new_pending_withdraw_requests_notification_freq.text.strip()
            == new_frequency
        )

    def test_withdraw_requests_notification_never(self, session, driver):
        """Test to verify registration new pending submission notifications settings
        for a given moderator."""
        moderator_settings_page = ModeratorSettingsPage(driver)
        moderator_settings_page.goto_short()
        assert ModeratorSettingsPage(driver, verify=True)
        initial_frequency = (
            moderator_settings_page.new_pending_withdraw_requests_notification_freq.text.strip()
        )
        new_frequency = 'Never'
        assert initial_frequency != new_frequency
        moderator_settings_page.select_from_withdraw_requests_dropdown(new_frequency)
        utils.wait_until_page_ready(driver)
        assert (
            moderator_settings_page.new_pending_withdraw_requests_notification_freq.text.strip()
            == new_frequency
        )

    def test_withdraw_requests_notification_instant(self, session, driver):
        """Test to verify registration new pending submission notifications settings
        for a given moderator."""
        moderator_settings_page = ModeratorSettingsPage(driver)
        moderator_settings_page.goto_short()
        assert ModeratorSettingsPage(driver, verify=True)
        initial_frequency = (
            moderator_settings_page.new_pending_withdraw_requests_notification_freq.text.strip()
        )
        new_frequency = 'Instant'
        assert initial_frequency != new_frequency
        moderator_settings_page.select_from_withdraw_requests_dropdown(new_frequency)
        utils.wait_until_page_ready(driver)
        assert (
            moderator_settings_page.new_pending_withdraw_requests_notification_freq.text.strip()
            == new_frequency
        )

    def test_user_settings_link(self, session, driver):
        """Test to verify registration new pending submission notifications settings
        for a given moderator."""
        moderator_settings_page = ModeratorSettingsPage(driver)
        moderator_settings_page.goto_short()
        assert ModeratorSettingsPage(driver, verify=True)
        moderator_settings_page.user_settings_link.click()
        utils.wait_until_page_ready(driver)

        user_settings_page = SettingsNotificationsPage(driver)
        user_settings_page.goto_short()
        user_settings_page.notifications_section.is_displayed()
        current_url = driver.current_url
        assert 'settings/notifications' in current_url
