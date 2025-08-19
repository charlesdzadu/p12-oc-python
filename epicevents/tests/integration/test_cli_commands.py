"""
Integration tests for CLI commands
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
from epicevents.cli.main import cli
from epicevents.app.auth.models import User, Department
from epicevents.app.auth.utils import create_access_token
import tempfile
from pathlib import Path


def test_cli_init_command(cli_runner):
    """Test database initialization command"""
    with patch("epicevents.cli.main.init_database") as mock_init:
        result = cli_runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "Database initialized successfully" in result.output
        mock_init.assert_called_once()


def test_cli_login_command(cli_runner, commercial_user):
    """Test login command"""
    with patch("epicevents.app.auth.service.AuthService.authenticate") as mock_auth:
        with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
            token = "test_token_123"
            mock_auth.return_value = token
            mock_get_user.return_value = commercial_user

            result = cli_runner.invoke(
                cli, ["auth", "login", "--email", "test@example.com"], input="password123\n"
            )

            assert result.exit_code == 0
            assert "Welcome" in result.output


def test_cli_login_invalid(cli_runner):
    """Test login with invalid credentials"""
    with patch("epicevents.app.auth.service.AuthService.authenticate") as mock_auth:
        mock_auth.return_value = None

        result = cli_runner.invoke(
            cli, ["auth", "login", "--email", "invalid@example.com"], input="wrongpassword\n"
        )

        assert "Invalid email or password" in result.output


def test_cli_logout_command(cli_runner):
    """Test logout command"""
    with patch("epicevents.app.auth.utils.remove_token") as mock_remove:
        result = cli_runner.invoke(cli, ["auth", "logout"])
        assert result.exit_code == 0
        assert "Logged out successfully" in result.output
        mock_remove.assert_called_once()


def test_cli_whoami_command(cli_runner, commercial_user):
    """Test whoami command"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        mock_get_user.return_value = commercial_user

        result = cli_runner.invoke(cli, ["auth", "whoami"])
        assert result.exit_code == 0
        assert "Test Commercial" in result.output
        assert "commercial@test.com" in result.output
        assert "COMMERCIAL" in result.output


def test_cli_whoami_not_logged_in(cli_runner):
    """Test whoami when not logged in"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        mock_get_user.return_value = None

        result = cli_runner.invoke(cli, ["auth", "whoami"])
        assert "Not logged in" in result.output


def test_cli_client_list(cli_runner, commercial_user, sample_client):
    """Test client list command"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        with patch(
            "epicevents.app.services.client_service.ClientService.list_clients"
        ) as mock_list:
            mock_get_user.return_value = commercial_user
            mock_list.return_value = [sample_client]

            result = cli_runner.invoke(cli, ["client", "list"])
            assert result.exit_code == 0
            assert "John Doe" in result.output
            assert "Example Corp" in result.output


def test_cli_client_create(cli_runner, commercial_user):
    """Test client create command"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        with patch(
            "epicevents.app.services.client_service.ClientService.create_client"
        ) as mock_create:
            mock_get_user.return_value = commercial_user
            mock_client = Mock(id=1)
            mock_create.return_value = mock_client

            result = cli_runner.invoke(
                cli,
                ["client", "create"],
                input="Test Client\ntest@client.com\n+33612345678\nTest Company\n",
            )

            assert result.exit_code == 0
            assert "Client created with ID: 1" in result.output


def test_cli_client_update(cli_runner, commercial_user, sample_client):
    """Test client update command"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        with patch(
            "epicevents.app.services.client_service.ClientService.update_client"
        ) as mock_update:
            mock_get_user.return_value = commercial_user
            mock_update.return_value = sample_client

            result = cli_runner.invoke(
                cli, ["client", "update", "1", "--full-name", "Updated Name"]
            )

            assert result.exit_code == 0
            assert "updated successfully" in result.output


def test_cli_client_search(cli_runner, commercial_user, sample_client):
    """Test client search command"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        with patch(
            "epicevents.app.services.client_service.ClientService.search_clients"
        ) as mock_search:
            mock_get_user.return_value = commercial_user
            mock_search.return_value = [sample_client]

            result = cli_runner.invoke(cli, ["client", "search", "John"])
            assert result.exit_code == 0
            assert "John Doe" in result.output


def test_cli_contract_list(cli_runner, commercial_user, sample_contract):
    """Test contract list command"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        with patch(
            "epicevents.app.services.contract_service.ContractService.list_contracts"
        ) as mock_list:
            mock_get_user.return_value = commercial_user
            sample_contract.client.full_name = "Test Client"
            mock_list.return_value = [sample_contract]

            result = cli_runner.invoke(cli, ["contract", "list"])
            assert result.exit_code == 0


def test_cli_contract_create(cli_runner, management_user):
    """Test contract create command"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        with patch(
            "epicevents.app.services.contract_service.ContractService.create_contract"
        ) as mock_create:
            mock_get_user.return_value = management_user
            mock_contract = Mock(id=1)
            mock_create.return_value = mock_contract

            result = cli_runner.invoke(cli, ["contract", "create"], input="1\n10000\n5000\n")

            assert result.exit_code == 0
            assert "Contract created with ID: 1" in result.output


def test_cli_contract_sign(cli_runner, commercial_user):
    """Test contract sign command"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        with patch(
            "epicevents.app.services.contract_service.ContractService.sign_contract"
        ) as mock_sign:
            mock_get_user.return_value = commercial_user
            mock_contract = Mock(id=1)
            mock_sign.return_value = mock_contract

            result = cli_runner.invoke(cli, ["contract", "sign", "1"])
            assert result.exit_code == 0
            assert "signed successfully" in result.output


def test_cli_event_list(cli_runner, support_user, sample_event):
    """Test event list command"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        with patch("epicevents.app.services.event_service.EventService.list_events") as mock_list:
            mock_get_user.return_value = support_user
            mock_list.return_value = [sample_event]

            result = cli_runner.invoke(cli, ["event", "list"])
            assert result.exit_code == 0
            assert "Annual Conference" in result.output


def test_cli_event_create(cli_runner, commercial_user):
    """Test event create command"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        with patch(
            "epicevents.app.services.event_service.EventService.create_event"
        ) as mock_create:
            mock_get_user.return_value = commercial_user
            mock_event = Mock(id=1)
            mock_create.return_value = mock_event

            result = cli_runner.invoke(
                cli,
                ["event", "create"],
                input="Test Event\n1\n2024-12-01 10:00\n2024-12-02 18:00\nTest Location\n100\nTest notes\n",
            )

            assert result.exit_code == 0
            assert "Event created with ID: 1" in result.output


def test_cli_user_list(cli_runner, management_user):
    """Test user list command (management only)"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        with patch("epicevents.app.database.get_session") as mock_session:
            mock_get_user.return_value = management_user
            mock_session.return_value.__enter__.return_value.exec.return_value.all.return_value = [
                management_user
            ]

            result = cli_runner.invoke(cli, ["user", "list"])
            assert result.exit_code == 0


def test_cli_user_list_no_permission(cli_runner, commercial_user):
    """Test user list without permission"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        mock_get_user.return_value = commercial_user

        result = cli_runner.invoke(cli, ["user", "list"])
        assert "Only management can view all users" in result.output


def test_cli_user_create(cli_runner, management_user):
    """Test user create command"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        with patch("epicevents.app.auth.service.AuthService.create_user") as mock_create:
            mock_get_user.return_value = management_user
            mock_user = Mock(id=1)
            mock_create.return_value = mock_user

            result = cli_runner.invoke(
                cli,
                ["user", "create"],
                input="EMP001\nTest User\ntest@user.com\nCOMMERCIAL\npassword123\npassword123\n",
            )

            assert result.exit_code == 0
            assert "User created with ID: 1" in result.output


def test_cli_not_logged_in_message(cli_runner):
    """Test commands show proper message when not logged in"""
    with patch("epicevents.app.utils.permissions.get_current_user") as mock_get_user:
        mock_get_user.return_value = None

        # Test client list
        result = cli_runner.invoke(cli, ["client", "list"])
        assert "Please login first" in result.output

        # Test contract list
        result = cli_runner.invoke(cli, ["contract", "list"])
        assert "Please login first" in result.output

        # Test event list
        result = cli_runner.invoke(cli, ["event", "list"])
        assert "Please login first" in result.output


def test_cli_help_commands(cli_runner):
    """Test help commands"""
    # Main help
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Epic Events CRM" in result.output

    # Auth help
    result = cli_runner.invoke(cli, ["auth", "--help"])
    assert result.exit_code == 0
    assert "Authentication commands" in result.output

    # Client help
    result = cli_runner.invoke(cli, ["client", "--help"])
    assert result.exit_code == 0
    assert "Client management commands" in result.output


def test_cli_version(cli_runner):
    """Test version command"""
    result = cli_runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()
