import pytest
from unittest.mock import patch, MagicMock
from epicevents.app.auth import (
    AuthService,
    Department,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    save_token,
    load_token,
    remove_token,
)
from epicevents.app.auth.models import User
from epicevents.app.auth.utils import ph
from pathlib import Path
import jwt
from datetime import datetime, timedelta, timezone


def test_password_hashing():
    """Test password hashing and verification"""
    password = "testpassword123"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_jwt_token_creation():
    """Test JWT token creation and validation"""
    data = {"user_id": 1, "email": "test@example.com"}
    token = create_access_token(data)

    assert token is not None
    assert isinstance(token, str)

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["user_id"] == 1
    assert decoded["email"] == "test@example.com"


def test_jwt_token_expiration():
    """Test JWT token expiration"""
    with patch("epicevents.app.auth.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        data = {"user_id": 1}
        token = create_access_token(data)

        # Simulate expired token
        with patch("jwt.decode", side_effect=jwt.ExpiredSignatureError):
            result = decode_access_token(token)
            assert result is None


def test_invalid_token():
    """Test invalid token handling"""
    invalid_token = "invalid.token.here"
    result = decode_access_token(invalid_token)
    assert result is None


def test_token_file_operations(temp_token_file, monkeypatch):
    """Test token save, load, and remove operations"""
    monkeypatch.setattr("epicevents.app.config.TOKEN_FILE", temp_token_file)

    test_token = "test_token_123"

    # Test save
    save_token(test_token)
    assert temp_token_file.exists()

    # Test load
    loaded_token = load_token()
    assert loaded_token == test_token

    # Test remove
    remove_token()
    assert not temp_token_file.exists()

    # Test load when file doesn't exist
    assert load_token() is None


def test_create_user(test_session, mock_get_session, monkeypatch):
    """Test user creation"""
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)

    user = AuthService.create_user(
        employee_id="TEST001",
        full_name="Test User",
        email="test@example.com",
        password="password123",
        department=Department.COMMERCIAL,
    )

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.department == Department.COMMERCIAL
    assert user.is_active


def test_create_user_duplicate(test_session, mock_get_session, monkeypatch):
    """Test creating duplicate user"""
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)

    # Create first user
    AuthService.create_user(
        employee_id="TEST001",
        full_name="Test User",
        email="duplicate@example.com",
        password="password123",
        department=Department.COMMERCIAL,
    )

    # Try to create duplicate
    with pytest.raises(ValueError, match="already exists"):
        AuthService.create_user(
            employee_id="TEST001",
            full_name="Another User",
            email="another@example.com",
            password="password123",
            department=Department.SUPPORT,
        )


def test_authenticate_user(test_session, mock_get_session, monkeypatch):
    """Test user authentication"""
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)

    AuthService.create_user(
        employee_id="TEST002",
        full_name="Auth Test User",
        email="auth@example.com",
        password="password123",
        department=Department.SUPPORT,
    )

    token = AuthService.authenticate("auth@example.com", "password123")
    assert token is not None

    invalid_token = AuthService.authenticate("auth@example.com", "wrongpassword")
    assert invalid_token is None

    # Test with non-existent user
    invalid_user = AuthService.authenticate("nonexistent@example.com", "password123")
    assert invalid_user is None


def test_authenticate_inactive_user(test_session, mock_get_session, monkeypatch):
    """Test authentication with inactive user"""
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)

    # Create inactive user
    user = User(
        employee_id="INACTIVE001",
        full_name="Inactive User",
        email="inactive@example.com",
        password_hash=hash_password("password123"),
        department=Department.COMMERCIAL,
        is_active=False,
    )
    test_session.add(user)
    test_session.commit()

    # Try to authenticate
    token = AuthService.authenticate("inactive@example.com", "password123")
    assert token is None


def test_get_current_user(test_session, mock_get_session, monkeypatch, commercial_user):
    """Test getting current user from token"""
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)

    # Create token
    token_data = {"user_id": commercial_user.id, "email": commercial_user.email}
    token = create_access_token(token_data)

    # Get user from token
    user = AuthService.get_current_user(token)
    assert user is not None
    assert user.id == commercial_user.id
    assert user.email == commercial_user.email

    # Test with invalid token
    invalid_user = AuthService.get_current_user("invalid_token")
    assert invalid_user is None


def test_update_user(test_session, mock_get_session, monkeypatch, commercial_user):
    """Test user update"""
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)

    updated_user = AuthService.update_user(
        user_id=commercial_user.id, full_name="Updated Name", department=Department.SUPPORT
    )

    assert updated_user.full_name == "Updated Name"
    assert updated_user.department == Department.SUPPORT

    # Test update non-existent user
    with pytest.raises(ValueError, match="User not found"):
        AuthService.update_user(user_id=99999, full_name="Test")


def test_change_password(test_session, mock_get_session, monkeypatch, commercial_user):
    """Test password change"""
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)

    result = AuthService.change_password(commercial_user.id, "newpassword123")
    assert result is True

    # Verify new password works
    test_session.refresh(commercial_user)
    assert verify_password("newpassword123", commercial_user.password_hash)

    # Test change password for non-existent user
    result = AuthService.change_password(99999, "password")
    assert result is False


def test_delete_user(test_session, mock_get_session, monkeypatch):
    """Test user deletion"""
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)

    # Create a user to delete
    user = AuthService.create_user(
        employee_id="DELETE001",
        full_name="To Delete",
        email="delete@example.com",
        password="password123",
        department=Department.SUPPORT,
    )

    # Delete the user
    result = AuthService.delete_user(user.id)
    assert result is True

    # Verify user is deleted
    deleted_user = test_session.get(User, user.id)
    assert deleted_user is None

    # Test delete non-existent user
    result = AuthService.delete_user(99999)
    assert result is False


def test_user_permissions():
    """Test user permission system"""
    management_user = User(
        employee_id="MGT001",
        full_name="Manager",
        email="manager@test.com",
        password_hash="hash",
        department=Department.MANAGEMENT,
    )

    commercial_user = User(
        employee_id="COM001",
        full_name="Commercial",
        email="commercial@test.com",
        password_hash="hash",
        department=Department.COMMERCIAL,
    )

    support_user = User(
        employee_id="SUP001",
        full_name="Support",
        email="support@test.com",
        password_hash="hash",
        department=Department.SUPPORT,
    )

    assert management_user.has_permission("create", "user")
    assert management_user.has_permission("delete", "user")
    assert not commercial_user.has_permission("create", "user")
    assert not support_user.has_permission("create", "client")

    assert commercial_user.has_permission("create", "client")
    assert commercial_user.has_permission("create", "event")
    assert not commercial_user.has_permission("delete", "user")

    assert support_user.has_permission("update", "event")
    assert not support_user.has_permission("create", "contract")


def test_user_department_properties():
    """Test user department property methods"""
    management_user = User(
        employee_id="MGT002",
        full_name="Manager2",
        email="manager2@test.com",
        password_hash="hash",
        department=Department.MANAGEMENT,
    )

    commercial_user = User(
        employee_id="COM002",
        full_name="Commercial2",
        email="commercial2@test.com",
        password_hash="hash",
        department=Department.COMMERCIAL,
    )

    support_user = User(
        employee_id="SUP002",
        full_name="Support2",
        email="support2@test.com",
        password_hash="hash",
        department=Department.SUPPORT,
    )

    # Test is_management property
    assert management_user.is_management is True
    assert commercial_user.is_management is False
    assert support_user.is_management is False

    # Test is_commercial property
    assert management_user.is_commercial is False
    assert commercial_user.is_commercial is True
    assert support_user.is_commercial is False

    # Test is_support property
    assert management_user.is_support is False
    assert commercial_user.is_support is False
    assert support_user.is_support is True


def test_department_enum():
    """Test Department enum values"""
    assert Department.MANAGEMENT.value == "MANAGEMENT"
    assert Department.COMMERCIAL.value == "COMMERCIAL"
    assert Department.SUPPORT.value == "SUPPORT"

    # Test enum membership
    assert Department.MANAGEMENT in Department
    assert "MANAGEMENT" in [d.value for d in Department]
