"""
Unit tests for service layer
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
from epicevents.app.services import ClientService, ContractService, EventService
from epicevents.app.auth.models import User, Department
from epicevents.app.models import Client, Contract, Event


def test_client_service_create(mock_get_session, commercial_user, monkeypatch):
    """Test creating client through service"""
    monkeypatch.setattr("epicevents.app.services.client_service.get_session", mock_get_session)

    client = ClientService.create_client(
        full_name="Service Test Client",
        email="service@example.com",
        phone="+33611111111",
        company_name="Service Corp",
        commercial_id=commercial_user.id,
        current_user=commercial_user,
    )

    assert client.email == "service@example.com"
    assert client.commercial_id == commercial_user.id


def test_client_service_create_no_permission(mock_get_session, support_user, monkeypatch):
    """Test creating client without permission"""
    monkeypatch.setattr("epicevents.app.services.client_service.get_session", mock_get_session)

    with pytest.raises(PermissionError, match="don't have permission"):
        ClientService.create_client(
            full_name="Unauthorized Client",
            email="unauth@example.com",
            phone="+33622222222",
            company_name="Unauth Corp",
            commercial_id=support_user.id,
            current_user=support_user,
        )


def test_client_service_create_duplicate_email(
    mock_get_session, commercial_user, sample_client, monkeypatch
):
    """Test creating client with duplicate email"""
    monkeypatch.setattr("epicevents.app.services.client_service.get_session", mock_get_session)

    with pytest.raises(ValueError, match="already exists"):
        ClientService.create_client(
            full_name="Duplicate Client",
            email=sample_client.email,  # Use existing email
            phone="+33633333333",
            company_name="Duplicate Corp",
            commercial_id=commercial_user.id,
            current_user=commercial_user,
        )


def test_client_service_update(mock_get_session, commercial_user, sample_client, monkeypatch):
    """Test updating client"""
    monkeypatch.setattr("epicevents.app.services.client_service.get_session", mock_get_session)

    updated = ClientService.update_client(
        client_id=sample_client.id,
        current_user=commercial_user,
        full_name="Updated Service Name",
        phone="+33644444444",
    )

    assert updated.full_name == "Updated Service Name"
    assert updated.phone == "+33644444444"


def test_client_service_update_not_own_client(mock_get_session, commercial_user, monkeypatch):
    """Test updating client not owned by commercial"""
    monkeypatch.setattr("epicevents.app.services.client_service.get_session", mock_get_session)

    # Create another commercial
    other_commercial = User(
        id=999,
        employee_id="COM999",
        full_name="Other Commercial",
        email="other@test.com",
        password_hash="hash",
        department=Department.COMMERCIAL,
    )

    # Create client for other commercial
    other_client = Client(
        id=999,
        full_name="Other Client",
        email="otherclient@example.com",
        phone="+33655555555",
        company_name="Other Corp",
        commercial_id=other_commercial.id,
    )

    with patch(
        "epicevents.app.repositories.client_repo.ClientRepository.get_by_id",
        return_value=other_client,
    ):
        with pytest.raises(PermissionError, match="only update your own clients"):
            ClientService.update_client(
                client_id=other_client.id, current_user=commercial_user, full_name="Hacked Name"
            )


def test_client_service_list(mock_get_session, commercial_user, sample_client, monkeypatch):
    """Test listing clients"""
    monkeypatch.setattr("epicevents.app.services.client_service.get_session", mock_get_session)

    clients = ClientService.list_clients(commercial_user)
    assert len(clients) >= 1


def test_client_service_search(mock_get_session, commercial_user, sample_client, monkeypatch):
    """Test searching clients"""
    monkeypatch.setattr("epicevents.app.services.client_service.get_session", mock_get_session)

    results = ClientService.search_clients("John", commercial_user)
    assert len(results) >= 1
    assert any(c.full_name == "John Doe" for c in results)


def test_contract_service_create(mock_get_session, management_user, sample_client, monkeypatch):
    """Test creating contract through service"""
    monkeypatch.setattr("epicevents.app.services.contract_service.get_session", mock_get_session)

    contract = ContractService.create_contract(
        client_id=sample_client.id,
        total_amount=Decimal("20000.00"),
        amount_due=Decimal("20000.00"),
        commercial_id=management_user.id,
        current_user=management_user,
    )

    assert contract.total_amount == Decimal("20000.00")
    assert contract.client_id == sample_client.id


def test_contract_service_create_no_permission(
    mock_get_session, commercial_user, sample_client, monkeypatch
):
    """Test creating contract without permission"""
    monkeypatch.setattr("epicevents.app.services.contract_service.get_session", mock_get_session)

    with pytest.raises(PermissionError):
        ContractService.create_contract(
            client_id=sample_client.id,
            total_amount=Decimal("10000.00"),
            amount_due=Decimal("10000.00"),
            commercial_id=commercial_user.id,
            current_user=commercial_user,
        )


def test_contract_service_sign(mock_get_session, commercial_user, sample_contract, monkeypatch):
    """Test signing contract"""
    monkeypatch.setattr("epicevents.app.services.contract_service.get_session", mock_get_session)

    with patch("epicevents.app.utils.logging.log_contract_signed"):
        signed = ContractService.sign_contract(sample_contract.id, commercial_user)
        assert signed.signed is True


def test_contract_service_sign_already_signed(
    mock_get_session, commercial_user, signed_contract, monkeypatch
):
    """Test signing already signed contract"""
    monkeypatch.setattr("epicevents.app.services.contract_service.get_session", mock_get_session)

    with pytest.raises(ValueError, match="already signed"):
        ContractService.sign_contract(signed_contract.id, commercial_user)


def test_contract_service_update_payment(
    mock_get_session, commercial_user, sample_contract, monkeypatch
):
    """Test updating contract payment"""
    monkeypatch.setattr("epicevents.app.services.contract_service.get_session", mock_get_session)

    sample_contract.total_amount = Decimal("10000.00")
    sample_contract.amount_due = Decimal("10000.00")

    updated = ContractService.update_payment(
        sample_contract.id, Decimal("3000.00"), commercial_user
    )

    assert updated.amount_due == Decimal("7000.00")


def test_contract_service_list_filters(
    mock_get_session, commercial_user, sample_contract, monkeypatch
):
    """Test listing contracts with filters"""
    monkeypatch.setattr("epicevents.app.services.contract_service.get_session", mock_get_session)

    # Test unsigned filter
    unsigned = ContractService.list_contracts(commercial_user, unsigned_only=True)
    assert all(not c.signed for c in unsigned)

    # Test unpaid filter
    sample_contract.amount_due = Decimal("1000.00")
    unpaid = ContractService.list_contracts(commercial_user, unpaid_only=True)
    assert all(c.amount_due > 0 for c in unpaid)


def test_event_service_create(mock_get_session, commercial_user, signed_contract, monkeypatch):
    """Test creating event through service"""
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)

    event = EventService.create_event(
        name="Service Test Event",
        contract_id=signed_contract.id,
        event_date_start=datetime.now() + timedelta(days=10),
        event_date_end=datetime.now() + timedelta(days=11),
        location="Service Location",
        attendees=100,
        notes="Service test notes",
        current_user=commercial_user,
    )

    assert event.name == "Service Test Event"
    assert event.contract_id == signed_contract.id


def test_event_service_create_unsigned_contract(
    mock_get_session, commercial_user, sample_contract, monkeypatch
):
    """Test creating event for unsigned contract"""
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)

    sample_contract.signed = False

    with pytest.raises(ValueError, match="unsigned contract"):
        EventService.create_event(
            name="Invalid Event",
            contract_id=sample_contract.id,
            event_date_start=datetime.now() + timedelta(days=10),
            event_date_end=datetime.now() + timedelta(days=11),
            location="Invalid Location",
            attendees=50,
            notes=None,
            current_user=commercial_user,
        )


def test_event_service_update(mock_get_session, support_user, sample_event, monkeypatch):
    """Test updating event"""
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)

    updated = EventService.update_event(
        event_id=sample_event.id,
        current_user=support_user,
        name="Updated Event Name",
        attendees=200,
    )

    assert updated.name == "Updated Event Name"
    assert updated.attendees == 200


def test_event_service_update_not_assigned(
    mock_get_session, support_user, sample_event, monkeypatch
):
    """Test updating event not assigned to support user"""
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)

    # Create another support user
    other_support = User(
        id=998,
        employee_id="SUP998",
        full_name="Other Support",
        email="othersupport@test.com",
        password_hash="hash",
        department=Department.SUPPORT,
    )

    sample_event.support_contact_id = 999  # Different support user

    with pytest.raises(PermissionError, match="only update events assigned to you"):
        EventService.update_event(
            event_id=sample_event.id, current_user=other_support, name="Unauthorized Update"
        )


def test_event_service_assign_support(
    mock_get_session, management_user, sample_event, support_user, monkeypatch
):
    """Test assigning support contact to event"""
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)

    sample_event.support_contact_id = None

    with patch(
        "epicevents.app.auth.service.AuthService.get_current_user", return_value=support_user
    ):
        updated = EventService.assign_support_contact(
            event_id=sample_event.id,
            support_contact_id=support_user.id,
            current_user=management_user,
        )

        assert updated.support_contact_id == support_user.id


def test_event_service_assign_support_no_permission(
    mock_get_session, commercial_user, sample_event, support_user, monkeypatch
):
    """Test assigning support without permission"""
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)

    with pytest.raises(PermissionError, match="Only management"):
        EventService.assign_support_contact(
            event_id=sample_event.id,
            support_contact_id=support_user.id,
            current_user=commercial_user,
        )


def test_event_service_list_filters(mock_get_session, support_user, sample_event, monkeypatch):
    """Test listing events with filters"""
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)

    # Test upcoming filter
    upcoming = EventService.list_events(support_user, upcoming_only=True)
    assert all(e.event_date_start > datetime.utcnow() for e in upcoming)

    # Test without support filter
    sample_event.support_contact_id = None
    without_support = EventService.list_events(support_user, without_support=True)
    assert all(e.support_contact_id is None for e in without_support)


def test_event_service_search_by_location(
    mock_get_session, support_user, sample_event, monkeypatch
):
    """Test searching events by location"""
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)

    results = EventService.search_events_by_location("Paris", support_user)
    assert len(results) >= 1
    assert all("Paris" in e.location for e in results)


def test_service_permission_checks():
    """Test that services check permissions properly"""
    # Create users with different departments
    management = User(
        id=1,
        employee_id="MGT001",
        full_name="Manager",
        email="manager@test.com",
        password_hash="hash",
        department=Department.MANAGEMENT,
    )

    commercial = User(
        id=2,
        employee_id="COM001",
        full_name="Commercial",
        email="commercial@test.com",
        password_hash="hash",
        department=Department.COMMERCIAL,
    )

    support = User(
        id=3,
        employee_id="SUP001",
        full_name="Support",
        email="support@test.com",
        password_hash="hash",
        department=Department.SUPPORT,
    )

    # Test client permissions
    assert commercial.has_permission("create", "client")
    assert not support.has_permission("create", "client")

    # Test contract permissions
    assert management.has_permission("create", "contract")
    assert not commercial.has_permission("create", "contract")

    # Test event permissions
    assert commercial.has_permission("create", "event")
    assert support.has_permission("update", "event")
    assert not support.has_permission("create", "event")
