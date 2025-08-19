"""
Unit tests for utility functions
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from epicevents.app.utils import (
    get_current_user,
    require_auth,
    require_department,
    require_permission,
    init_sentry,
    log_action,
    log_user_creation,
    log_user_modification,
    log_contract_signed,
    log_error,
    log_security_event,
)
from epicevents.app.auth.models import User, Department
from epicevents.app.auth.utils import save_token, create_access_token
import sentry_sdk


def test_get_current_user_with_valid_token(temp_token_file, commercial_user, monkeypatch):
    """Test getting current user with valid token"""
    monkeypatch.setattr("epicevents.app.config.TOKEN_FILE", temp_token_file)

    # Create and save a valid token
    token_data = {
        "user_id": commercial_user.id,
        "email": commercial_user.email,
        "department": commercial_user.department.value,
    }
    token = create_access_token(token_data)
    save_token(token)

    with patch(
        "epicevents.app.auth.service.AuthService.get_current_user", return_value=commercial_user
    ):
        user = get_current_user()
        assert user is not None
        assert user.id == commercial_user.id


def test_get_current_user_no_token(temp_token_file, monkeypatch):
    """Test getting current user with no token"""
    monkeypatch.setattr("epicevents.app.config.TOKEN_FILE", temp_token_file)

    user = get_current_user()
    assert user is None


def test_require_auth_decorator(commercial_user):
    """Test require_auth decorator"""
    with patch("epicevents.app.utils.permissions.get_current_user", return_value=commercial_user):

        @require_auth
        def protected_function(value, current_user=None):
            assert current_user is not None
            assert current_user.id == commercial_user.id
            return value * 2

        result = protected_function(5)
        assert result == 10


def test_require_auth_decorator_no_user():
    """Test require_auth decorator without authenticated user"""
    with patch("epicevents.app.utils.permissions.get_current_user", return_value=None):

        @require_auth
        def protected_function(value, current_user=None):
            return value * 2

        with pytest.raises(PermissionError, match="Authentication required"):
            protected_function(5)


def test_require_department_decorator(commercial_user, support_user):
    """Test require_department decorator"""

    @require_department(Department.COMMERCIAL, Department.MANAGEMENT)
    def commercial_only_function(value, current_user=None):
        return value * 3

    # Test with commercial user (allowed)
    with patch("epicevents.app.utils.permissions.get_current_user", return_value=commercial_user):
        result = commercial_only_function(4)
        assert result == 12

    # Test with support user (not allowed)
    with patch("epicevents.app.utils.permissions.get_current_user", return_value=support_user):
        with pytest.raises(PermissionError, match="requires one of the following departments"):
            commercial_only_function(4)


def test_require_permission_decorator(commercial_user, support_user):
    """Test require_permission decorator"""

    @require_permission("create", "client")
    def create_client_function(data, current_user=None):
        return f"Created client: {data}"

    # Test with commercial user (has permission)
    with patch("epicevents.app.utils.permissions.get_current_user", return_value=commercial_user):
        result = create_client_function("test")
        assert result == "Created client: test"

    # Test with support user (no permission)
    with patch("epicevents.app.utils.permissions.get_current_user", return_value=support_user):
        with pytest.raises(PermissionError, match="don't have permission"):
            create_client_function("test")


def test_init_sentry_with_dsn(monkeypatch):
    """Test Sentry initialization with DSN"""
    monkeypatch.setattr("epicevents.app.config.settings.sentry_dsn", "https://fake@sentry.io/123")
    monkeypatch.setattr("epicevents.app.config.settings.debug", False)
    monkeypatch.setattr("epicevents.app.config.settings.app_env", "production")

    with patch("sentry_sdk.init") as mock_init:
        init_sentry()
        mock_init.assert_called_once()
        args, kwargs = mock_init.call_args
        assert kwargs["dsn"] == "https://fake@sentry.io/123"
        assert kwargs["environment"] == "production"


def test_init_sentry_without_dsn(monkeypatch):
    """Test Sentry initialization without DSN"""
    monkeypatch.setattr("epicevents.app.config.settings.sentry_dsn", None)

    with patch("sentry_sdk.init") as mock_init:
        init_sentry()
        mock_init.assert_not_called()


def test_log_action_decorator_success(commercial_user):
    """Test log_action decorator on successful execution"""

    @log_action("Test Action")
    def test_function(value, current_user=None):
        return value * 2

    with patch("epicevents.app.utils.logging.logger.info") as mock_log:
        with patch("sentry_sdk.capture_message") as mock_sentry:
            result = test_function(5, current_user=commercial_user)
            assert result == 10
            mock_log.assert_called_with("Test Action - Success - User: commercial@test.com")


def test_log_action_decorator_failure(commercial_user):
    """Test log_action decorator on failure"""

    @log_action("Test Action")
    def failing_function(current_user=None):
        raise ValueError("Test error")

    with patch("epicevents.app.utils.logging.logger.error") as mock_log:
        with patch("sentry_sdk.capture_exception") as mock_sentry:
            with pytest.raises(ValueError):
                failing_function(current_user=commercial_user)
            mock_log.assert_called()
            assert "Failed" in mock_log.call_args[0][0]


def test_log_user_creation():
    """Test logging user creation"""
    with patch("epicevents.app.utils.logging.logger.info") as mock_log:
        with patch("sentry_sdk.capture_message") as mock_sentry:
            log_user_creation(1, "test@example.com", "COMMERCIAL")
            mock_log.assert_called_once()
            assert "User created" in mock_log.call_args[0][0]
            assert "test@example.com" in mock_log.call_args[0][0]


def test_log_user_modification():
    """Test logging user modification"""
    changes = {"department": "SUPPORT", "is_active": False}

    with patch("epicevents.app.utils.logging.logger.info") as mock_log:
        with patch("sentry_sdk.capture_message") as mock_sentry:
            log_user_modification(1, "admin@test.com", changes)
            mock_log.assert_called_once()
            assert "User modified" in mock_log.call_args[0][0]
            assert "admin@test.com" in mock_log.call_args[0][0]


def test_log_contract_signed():
    """Test logging contract signature"""
    with patch("epicevents.app.utils.logging.logger.info") as mock_log:
        with patch("sentry_sdk.capture_message") as mock_sentry:
            log_contract_signed(1, 2, "commercial@test.com")
            mock_log.assert_called_once()
            assert "Contract signed" in mock_log.call_args[0][0]


def test_log_error_with_context():
    """Test logging error with context"""
    error = ValueError("Test error")
    context = {"user": "test@example.com", "action": "create_client"}

    with patch("epicevents.app.utils.logging.logger.error") as mock_log:
        with patch("sentry_sdk.push_scope") as mock_scope:
            with patch("sentry_sdk.capture_exception") as mock_capture:
                log_error(error, context)
                mock_log.assert_called_once()
                mock_capture.assert_called_once()


def test_log_security_event():
    """Test logging security event"""
    with patch("epicevents.app.utils.logging.logger.warning") as mock_log:
        with patch("sentry_sdk.capture_message") as mock_sentry:
            log_security_event("login_failed", "hacker@evil.com", "Invalid password attempt")
            mock_log.assert_called_once()
            assert "Security Event" in mock_log.call_args[0][0]
            assert "login_failed" in mock_log.call_args[0][0]
            assert "hacker@evil.com" in mock_log.call_args[0][0]


def test_decorators_preserve_function_metadata():
    """Test that decorators preserve function metadata"""

    @require_auth
    def example_function():
        """Example docstring"""
        pass

    assert example_function.__name__ == "example_function"
    assert example_function.__doc__ == "Example docstring"

    @require_department(Department.MANAGEMENT)
    def management_function():
        """Management only"""
        pass

    assert management_function.__name__ == "management_function"
    assert management_function.__doc__ == "Management only"

    @require_permission("create", "user")
    def create_user_function():
        """Create user"""
        pass

    assert create_user_function.__name__ == "create_user_function"
    assert create_user_function.__doc__ == "Create user"


def test_multiple_decorators_stacking(management_user):
    """Test stacking multiple permission decorators"""

    @require_auth
    @require_department(Department.MANAGEMENT)
    @require_permission("create", "user")
    def highly_protected_function(value, current_user=None):
        return value * 10

    with patch("epicevents.app.utils.permissions.get_current_user", return_value=management_user):
        result = highly_protected_function(3)
        assert result == 30


def test_sentry_configuration_modes(monkeypatch):
    """Test different Sentry configuration modes"""
    # Test debug mode
    monkeypatch.setattr("epicevents.app.config.settings.sentry_dsn", "https://fake@sentry.io/123")
    monkeypatch.setattr("epicevents.app.config.settings.debug", True)

    with patch("sentry_sdk.init") as mock_init:
        init_sentry()
        _, kwargs = mock_init.call_args
        assert kwargs["traces_sample_rate"] == 1.0  # Full tracing in debug

    # Test production mode
    monkeypatch.setattr("epicevents.app.config.settings.debug", False)

    with patch("sentry_sdk.init") as mock_init:
        init_sentry()
        _, kwargs = mock_init.call_args
        assert kwargs["traces_sample_rate"] == 0.1  # Reduced tracing in production
