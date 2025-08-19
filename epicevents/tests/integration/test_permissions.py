"""
Integration tests for permission system
"""

import pytest
from unittest.mock import patch
from epicevents.app.auth.models import User, Department
from epicevents.app.services import ClientService, ContractService, EventService
from epicevents.app.utils.permissions import require_auth, require_department, require_permission
from decimal import Decimal
from datetime import datetime, timedelta


def test_department_permissions_matrix():
    """Test complete permission matrix for all departments"""
    # Define expected permissions
    permissions_matrix = {
        Department.MANAGEMENT: {
            "create": ["user", "contract", "event"],
            "update": ["user", "contract", "event"],
            "delete": ["user"],
            "read": ["user", "client", "contract", "event"],
        },
        Department.COMMERCIAL: {
            "create": ["client", "event"],
            "update": ["client", "contract"],
            "delete": [],
            "read": ["client", "contract", "event"],
        },
        Department.SUPPORT: {
            "create": [],
            "update": ["event"],
            "delete": [],
            "read": ["client", "contract", "event"],
        },
    }

    # Test each department
    for dept, expected_perms in permissions_matrix.items():
        user = User(
            id=1,
            employee_id=f"{dept.value[:3]}001",
            full_name=f"{dept.value} User",
            email=f"{dept.value.lower()}@test.com",
            password_hash="hash",
            department=dept,
        )

        for action, resources in expected_perms.items():
            for resource in ["user", "client", "contract", "event"]:
                should_have = resource in resources
                has_permission = user.has_permission(action, resource)
                assert (
                    has_permission == should_have
                ), f"{dept.value} should {'have' if should_have else 'not have'} {action} permission for {resource}"


def test_commercial_client_ownership(mock_get_session, monkeypatch):
    """Test commercials can only modify their own clients"""
    monkeypatch.setattr("epicevents.app.services.client_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)

    # Create two commercials
    from epicevents.app.auth.service import AuthService

    commercial1 = AuthService.create_user(
        employee_id="COM001",
        full_name="Commercial One",
        email="com1@test.com",
        password="password",
        department=Department.COMMERCIAL,
    )

    commercial2 = AuthService.create_user(
        employee_id="COM002",
        full_name="Commercial Two",
        email="com2@test.com",
        password="password",
        department=Department.COMMERCIAL,
    )

    # Commercial1 creates a client
    client = ClientService.create_client(
        full_name="Client for Com1",
        email="client1@test.com",
        phone="+33611111111",
        company_name="Company 1",
        commercial_id=commercial1.id,
        current_user=commercial1,
    )

    # Commercial1 can update their own client
    updated = ClientService.update_client(
        client_id=client.id, current_user=commercial1, full_name="Updated by Com1"
    )
    assert updated.full_name == "Updated by Com1"

    # Commercial2 cannot update Commercial1's client
    with patch(
        "epicevents.app.repositories.client_repo.ClientRepository.get_by_id", return_value=client
    ):
        with pytest.raises(PermissionError, match="only update your own clients"):
            ClientService.update_client(
                client_id=client.id, current_user=commercial2, full_name="Hacked by Com2"
            )


def test_support_event_assignment(mock_get_session, monkeypatch):
    """Test support can only update events assigned to them"""
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)

    from epicevents.app.auth.service import AuthService

    # Create support users
    support1 = AuthService.create_user(
        employee_id="SUP001",
        full_name="Support One",
        email="sup1@test.com",
        password="password",
        department=Department.SUPPORT,
    )

    support2 = AuthService.create_user(
        employee_id="SUP002",
        full_name="Support Two",
        email="sup2@test.com",
        password="password",
        department=Department.SUPPORT,
    )

    # Create an event assigned to support1
    from epicevents.app.models import Event

    event = Event(
        id=1,
        name="Test Event",
        contract_id=1,
        event_date_start=datetime.now() + timedelta(days=10),
        event_date_end=datetime.now() + timedelta(days=11),
        location="Test Location",
        attendees=100,
        support_contact_id=support1.id,
    )

    # Support1 can update their event
    with patch(
        "epicevents.app.repositories.event_repo.EventRepository.get_by_id", return_value=event
    ):
        with patch(
            "epicevents.app.repositories.event_repo.EventRepository.update", return_value=event
        ):
            updated = EventService.update_event(event_id=1, current_user=support1, attendees=150)
            assert updated is not None

    # Support2 cannot update Support1's event
    with patch(
        "epicevents.app.repositories.event_repo.EventRepository.get_by_id", return_value=event
    ):
        with pytest.raises(PermissionError, match="only update events assigned to you"):
            EventService.update_event(event_id=1, current_user=support2, attendees=200)


def test_management_full_access(mock_get_session, monkeypatch):
    """Test management has full access to all operations"""
    monkeypatch.setattr("epicevents.app.services.client_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.services.contract_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)

    from epicevents.app.auth.service import AuthService

    management = AuthService.create_user(
        employee_id="MGT001",
        full_name="Manager",
        email="manager@test.com",
        password="password",
        department=Department.MANAGEMENT,
    )

    commercial = AuthService.create_user(
        employee_id="COM003",
        full_name="Commercial",
        email="com3@test.com",
        password="password",
        department=Department.COMMERCIAL,
    )

    # Management can create contracts (commercial cannot)
    client = ClientService.create_client(
        full_name="Test Client",
        email="testclient@test.com",
        phone="+33611111111",
        company_name="Test Company",
        commercial_id=commercial.id,
        current_user=commercial,
    )

    contract = ContractService.create_contract(
        client_id=client.id,
        total_amount=Decimal("10000.00"),
        amount_due=Decimal("10000.00"),
        commercial_id=commercial.id,
        current_user=management,
    )
    assert contract is not None

    # Commercial cannot create contracts
    with pytest.raises(PermissionError):
        ContractService.create_contract(
            client_id=client.id,
            total_amount=Decimal("20000.00"),
            amount_due=Decimal("20000.00"),
            commercial_id=commercial.id,
            current_user=commercial,
        )

    # Management can update any client
    with patch(
        "epicevents.app.repositories.client_repo.ClientRepository.get_by_id", return_value=client
    ):
        with patch(
            "epicevents.app.repositories.client_repo.ClientRepository.update", return_value=client
        ):
            updated = ClientService.update_client(
                client_id=client.id, current_user=management, full_name="Updated by Management"
            )
            assert updated is not None


def test_cross_department_read_access(mock_get_session, monkeypatch):
    """Test all departments can read all data"""
    monkeypatch.setattr("epicevents.app.services.client_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.services.contract_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)

    from epicevents.app.auth.service import AuthService

    # Create users from each department
    users = []
    for dept in Department:
        user = AuthService.create_user(
            employee_id=f"{dept.value[:3]}100",
            full_name=f"{dept.value} Reader",
            email=f"{dept.value.lower()}.reader@test.com",
            password="password",
            department=dept,
        )
        users.append(user)

    # All users should be able to list clients, contracts, and events
    for user in users:
        # Should not raise PermissionError
        with patch(
            "epicevents.app.repositories.client_repo.ClientRepository.get_all", return_value=[]
        ):
            clients = ClientService.list_clients(user)
            assert clients is not None

        with patch(
            "epicevents.app.repositories.contract_repo.ContractRepository.get_all", return_value=[]
        ):
            contracts = ContractService.list_contracts(user)
            assert contracts is not None

        with patch(
            "epicevents.app.repositories.event_repo.EventRepository.get_all", return_value=[]
        ):
            events = EventService.list_events(user)
            assert events is not None


def test_decorator_based_permissions():
    """Test permission decorators work correctly"""

    # Test require_auth
    @require_auth
    def protected_function(value, current_user=None):
        return value * 2

    # Without user
    with patch("epicevents.app.utils.permissions.get_current_user", return_value=None):
        with pytest.raises(PermissionError, match="Authentication required"):
            protected_function(5)

    # With user
    mock_user = User(
        id=1,
        employee_id="TEST001",
        full_name="Test User",
        email="test@test.com",
        password_hash="hash",
        department=Department.COMMERCIAL,
    )

    with patch("epicevents.app.utils.permissions.get_current_user", return_value=mock_user):
        result = protected_function(5)
        assert result == 10

    # Test require_department
    @require_department(Department.MANAGEMENT)
    def management_only(value, current_user=None):
        return value * 3

    # Commercial user (should fail)
    with patch("epicevents.app.utils.permissions.get_current_user", return_value=mock_user):
        with pytest.raises(PermissionError, match="requires one of the following departments"):
            management_only(5)

    # Management user (should succeed)
    management_user = User(
        id=2,
        employee_id="MGT999",
        full_name="Manager",
        email="manager@test.com",
        password_hash="hash",
        department=Department.MANAGEMENT,
    )

    with patch("epicevents.app.utils.permissions.get_current_user", return_value=management_user):
        result = management_only(5)
        assert result == 15

    # Test require_permission
    @require_permission("create", "contract")
    def create_contract_function(data, current_user=None):
        return f"Contract: {data}"

    # Commercial (no permission)
    with patch("epicevents.app.utils.permissions.get_current_user", return_value=mock_user):
        with pytest.raises(PermissionError, match="don't have permission"):
            create_contract_function("test")

    # Management (has permission)
    with patch("epicevents.app.utils.permissions.get_current_user", return_value=management_user):
        result = create_contract_function("test")
        assert result == "Contract: test"


def test_event_creation_requires_signed_contract(mock_get_session, monkeypatch):
    """Test that events can only be created for signed contracts"""
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)

    from epicevents.app.auth.service import AuthService
    from epicevents.app.models import Contract

    commercial = AuthService.create_user(
        employee_id="COM100",
        full_name="Commercial",
        email="com100@test.com",
        password="password",
        department=Department.COMMERCIAL,
    )

    # Create unsigned contract
    unsigned_contract = Contract(
        id=1,
        client_id=1,
        commercial_id=commercial.id,
        total_amount=Decimal("10000.00"),
        amount_due=Decimal("10000.00"),
        signed=False,
    )

    # Try to create event for unsigned contract
    with patch(
        "epicevents.app.repositories.contract_repo.ContractRepository.get_by_id",
        return_value=unsigned_contract,
    ):
        with pytest.raises(ValueError, match="unsigned contract"):
            EventService.create_event(
                name="Invalid Event",
                contract_id=1,
                event_date_start=datetime.now() + timedelta(days=10),
                event_date_end=datetime.now() + timedelta(days=11),
                location="Location",
                attendees=100,
                notes=None,
                current_user=commercial,
            )

    # Sign the contract
    unsigned_contract.signed = True

    # Now event creation should work
    with patch(
        "epicevents.app.repositories.contract_repo.ContractRepository.get_by_id",
        return_value=unsigned_contract,
    ):
        with patch("epicevents.app.repositories.event_repo.EventRepository.create") as mock_create:
            mock_event = Event(
                id=1,
                name="Valid Event",
                contract_id=1,
                event_date_start=datetime.now() + timedelta(days=10),
                event_date_end=datetime.now() + timedelta(days=11),
                location="Location",
                attendees=100,
            )
            mock_create.return_value = mock_event

            event = EventService.create_event(
                name="Valid Event",
                contract_id=1,
                event_date_start=datetime.now() + timedelta(days=10),
                event_date_end=datetime.now() + timedelta(days=11),
                location="Location",
                attendees=100,
                notes=None,
                current_user=commercial,
            )
            assert event is not None
