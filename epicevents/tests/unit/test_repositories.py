"""
Unit tests for repository layer
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from epicevents.app.repositories import ClientRepository, ContractRepository, EventRepository
from epicevents.app.models import Client, Contract, Event
from epicevents.app.auth.models import User, Department


def test_client_repository_create(test_session, commercial_user):
    """Test creating a client through repository"""
    repo = ClientRepository(test_session)

    client = repo.create(
        full_name="Test Client",
        email="testclient@example.com",
        phone="+33612345678",
        company_name="Test Company",
        commercial_id=commercial_user.id,
    )

    assert client.id is not None
    assert client.email == "testclient@example.com"


def test_client_repository_get_by_id(test_session, sample_client):
    """Test getting client by ID"""
    repo = ClientRepository(test_session)

    client = repo.get_by_id(sample_client.id)
    assert client is not None
    assert client.id == sample_client.id

    # Test non-existent ID
    none_client = repo.get_by_id(99999)
    assert none_client is None


def test_client_repository_get_by_email(test_session, sample_client):
    """Test getting client by email"""
    repo = ClientRepository(test_session)

    client = repo.get_by_email(sample_client.email)
    assert client is not None
    assert client.email == sample_client.email

    # Test non-existent email
    none_client = repo.get_by_email("nonexistent@example.com")
    assert none_client is None


def test_client_repository_get_by_commercial(test_session, sample_client, commercial_user):
    """Test getting clients by commercial"""
    repo = ClientRepository(test_session)

    # Create another client for the same commercial
    repo.create(
        full_name="Another Client",
        email="another@example.com",
        phone="+33698765432",
        company_name="Another Company",
        commercial_id=commercial_user.id,
    )

    clients = repo.get_by_commercial(commercial_user.id)
    assert len(clients) == 2
    assert all(c.commercial_id == commercial_user.id for c in clients)


def test_client_repository_search_by_name(test_session, sample_client):
    """Test searching clients by name"""
    repo = ClientRepository(test_session)

    # Search by full name
    results = repo.search_by_name("John")
    assert len(results) == 1
    assert results[0].id == sample_client.id

    # Search by company name
    results = repo.search_by_name("Example")
    assert len(results) == 1

    # Search non-existent
    results = repo.search_by_name("NonExistent")
    assert len(results) == 0


def test_client_repository_get_clients_without_commercial(test_session):
    """Test getting clients without commercial"""
    repo = ClientRepository(test_session)

    # Create client without commercial
    repo.create(
        full_name="No Commercial Client",
        email="nocommercial@example.com",
        phone="+33611111111",
        company_name="No Commercial Corp",
        commercial_id=None,
    )

    clients = repo.get_clients_without_commercial()
    assert len(clients) >= 1
    assert all(c.commercial_id is None for c in clients)


def test_client_repository_assign_commercial(test_session, commercial_user):
    """Test assigning commercial to client"""
    repo = ClientRepository(test_session)

    # Create client without commercial
    client = repo.create(
        full_name="Assign Commercial Test",
        email="assigntest@example.com",
        phone="+33622222222",
        company_name="Assign Test Corp",
        commercial_id=None,
    )

    # Assign commercial
    updated_client = repo.assign_commercial(client.id, commercial_user.id)
    assert updated_client.commercial_id == commercial_user.id


def test_client_repository_update(test_session, sample_client):
    """Test updating client"""
    repo = ClientRepository(test_session)

    updated = repo.update(sample_client.id, full_name="Updated Name", phone="+33699999999")

    assert updated.full_name == "Updated Name"
    assert updated.phone == "+33699999999"


def test_client_repository_delete(test_session, commercial_user):
    """Test deleting client"""
    repo = ClientRepository(test_session)

    # Create a client to delete
    client = repo.create(
        full_name="To Delete",
        email="delete@example.com",
        phone="+33633333333",
        company_name="Delete Corp",
        commercial_id=commercial_user.id,
    )

    # Delete the client
    result = repo.delete(client.id)
    assert result is True

    # Verify deletion
    deleted = repo.get_by_id(client.id)
    assert deleted is None


def test_contract_repository_get_by_client(test_session, sample_client, sample_contract):
    """Test getting contracts by client"""
    repo = ContractRepository(test_session)

    contracts = repo.get_by_client(sample_client.id)
    assert len(contracts) == 1
    assert contracts[0].id == sample_contract.id


def test_contract_repository_get_by_commercial(test_session, sample_contract, commercial_user):
    """Test getting contracts by commercial"""
    repo = ContractRepository(test_session)

    contracts = repo.get_by_commercial(commercial_user.id)
    assert len(contracts) >= 1
    assert all(c.commercial_id == commercial_user.id for c in contracts)


def test_contract_repository_get_unsigned(test_session, sample_contract):
    """Test getting unsigned contracts"""
    repo = ContractRepository(test_session)

    # Ensure contract is unsigned
    sample_contract.signed = False
    test_session.commit()

    unsigned = repo.get_unsigned_contracts()
    assert len(unsigned) >= 1
    assert all(not c.signed for c in unsigned)


def test_contract_repository_get_unpaid(test_session, sample_contract):
    """Test getting unpaid contracts"""
    repo = ContractRepository(test_session)

    # Ensure contract has amount due
    sample_contract.amount_due = Decimal("1000.00")
    test_session.commit()

    unpaid = repo.get_unpaid_contracts()
    assert len(unpaid) >= 1
    assert all(c.amount_due > 0 for c in unpaid)


def test_contract_repository_sign_contract(test_session, sample_contract):
    """Test signing contract through repository"""
    repo = ContractRepository(test_session)

    sample_contract.signed = False
    test_session.commit()

    signed = repo.sign_contract(sample_contract.id)
    assert signed.signed is True


def test_contract_repository_update_payment(test_session, sample_contract):
    """Test updating contract payment"""
    repo = ContractRepository(test_session)

    sample_contract.total_amount = Decimal("10000.00")
    sample_contract.amount_due = Decimal("10000.00")
    test_session.commit()

    updated = repo.update_payment(sample_contract.id, Decimal("3000.00"))
    assert updated.amount_due == Decimal("7000.00")


def test_event_repository_get_by_contract(test_session, sample_event, signed_contract):
    """Test getting events by contract"""
    repo = EventRepository(test_session)

    events = repo.get_by_contract(signed_contract.id)
    assert len(events) == 1
    assert events[0].id == sample_event.id


def test_event_repository_get_by_support(test_session, sample_event, support_user):
    """Test getting events by support contact"""
    repo = EventRepository(test_session)

    events = repo.get_by_support_contact(support_user.id)
    assert len(events) >= 1
    assert all(e.support_contact_id == support_user.id for e in events)


def test_event_repository_get_without_support(test_session, signed_contract):
    """Test getting events without support"""
    repo = EventRepository(test_session)

    # Create event without support
    event = Event(
        name="No Support Event",
        contract_id=signed_contract.id,
        event_date_start=datetime.now() + timedelta(days=10),
        event_date_end=datetime.now() + timedelta(days=11),
        location="Test Location",
        attendees=50,
        support_contact_id=None,
    )
    test_session.add(event)
    test_session.commit()

    events = repo.get_events_without_support()
    assert len(events) >= 1
    assert all(e.support_contact_id is None for e in events)


def test_event_repository_get_upcoming(test_session, signed_contract):
    """Test getting upcoming events"""
    repo = EventRepository(test_session)

    # Create future event
    future_event = Event(
        name="Future Event",
        contract_id=signed_contract.id,
        event_date_start=datetime.now() + timedelta(days=60),
        event_date_end=datetime.now() + timedelta(days=61),
        location="Future Location",
        attendees=100,
    )
    test_session.add(future_event)
    test_session.commit()

    upcoming = repo.get_upcoming_events()
    assert len(upcoming) >= 1
    assert all(e.event_date_start > datetime.utcnow() for e in upcoming)


def test_event_repository_get_past(test_session, signed_contract):
    """Test getting past events"""
    repo = EventRepository(test_session)

    # Create past event
    past_event = Event(
        name="Past Event",
        contract_id=signed_contract.id,
        event_date_start=datetime.now() - timedelta(days=30),
        event_date_end=datetime.now() - timedelta(days=29),
        location="Past Location",
        attendees=75,
    )
    test_session.add(past_event)
    test_session.commit()

    past = repo.get_past_events()
    assert len(past) >= 1
    assert all(e.event_date_end < datetime.utcnow() for e in past)


def test_event_repository_get_date_range(test_session, signed_contract):
    """Test getting events in date range"""
    repo = EventRepository(test_session)

    start_date = datetime.now() + timedelta(days=20)
    end_date = datetime.now() + timedelta(days=40)

    # Create event in range
    event = Event(
        name="Range Event",
        contract_id=signed_contract.id,
        event_date_start=start_date + timedelta(days=5),
        event_date_end=start_date + timedelta(days=6),
        location="Range Location",
        attendees=60,
    )
    test_session.add(event)
    test_session.commit()

    events = repo.get_events_in_date_range(start_date, end_date)
    assert any(e.name == "Range Event" for e in events)


def test_event_repository_assign_support(test_session, signed_contract, support_user):
    """Test assigning support contact to event"""
    repo = EventRepository(test_session)

    # Create event without support
    event = repo.create(
        name="Assign Support Test",
        contract_id=signed_contract.id,
        event_date_start=datetime.now() + timedelta(days=15),
        event_date_end=datetime.now() + timedelta(days=16),
        location="Test Location",
        attendees=80,
        support_contact_id=None,
    )

    # Assign support
    updated = repo.assign_support_contact(event.id, support_user.id)
    assert updated.support_contact_id == support_user.id


def test_event_repository_search_by_location(test_session, sample_event):
    """Test searching events by location"""
    repo = EventRepository(test_session)

    results = repo.search_by_location("Paris")
    assert len(results) >= 1
    assert all("Paris" in e.location for e in results)

    # Search non-existent location
    results = repo.search_by_location("Antarctica")
    assert len(results) == 0


def test_base_repository_methods(test_session, sample_client):
    """Test base repository methods"""
    repo = ClientRepository(test_session)

    # Test get_all
    all_clients = repo.get_all()
    assert len(all_clients) >= 1

    # Test get_all with pagination
    paginated = repo.get_all(skip=0, limit=1)
    assert len(paginated) <= 1

    # Test count
    count = repo.count()
    assert count >= 1

    # Test filter_by
    filtered = repo.filter_by(company_name="Example Corp")
    assert len(filtered) >= 1
    assert all(c.company_name == "Example Corp" for c in filtered)
