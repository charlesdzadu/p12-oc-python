"""
Unit tests for domain models
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from epicevents.app.models import Client, Contract, Event
from epicevents.app.auth.models import User, Department


def test_client_model_creation(test_session, commercial_user):
    """Test client model creation and properties"""
    client = Client(
        full_name="John Doe",
        email="john@example.com",
        phone="+33612345678",
        company_name="Example Corp",
        commercial_id=commercial_user.id,
    )

    test_session.add(client)
    test_session.commit()

    assert client.id is not None
    assert client.full_name == "John Doe"
    assert client.email == "john@example.com"
    assert client.commercial_id == commercial_user.id
    assert isinstance(client.created_at, datetime)
    assert isinstance(client.updated_at, datetime)


def test_client_update_method(sample_client, test_session):
    """Test client update method"""
    original_updated_at = sample_client.updated_at

    sample_client.update(full_name="Jane Doe", phone="+33698765432")

    test_session.commit()
    test_session.refresh(sample_client)

    assert sample_client.full_name == "Jane Doe"
    assert sample_client.phone == "+33698765432"
    assert sample_client.updated_at > original_updated_at


def test_client_relationships(sample_client, sample_contract, test_session):
    """Test client relationships with contracts"""
    test_session.refresh(sample_client)
    assert len(sample_client.contracts) == 1
    assert sample_client.contracts[0].id == sample_contract.id


def test_client_repr(sample_client):
    """Test client string representation"""
    repr_str = repr(sample_client)
    assert "John Doe" in repr_str
    assert "Example Corp" in repr_str


def test_contract_model_creation(test_session, sample_client, commercial_user):
    """Test contract model creation"""
    contract = Contract(
        client_id=sample_client.id,
        commercial_id=commercial_user.id,
        total_amount=Decimal("15000.00"),
        amount_due=Decimal("10000.00"),
        signed=False,
    )

    test_session.add(contract)
    test_session.commit()

    assert contract.id is not None
    assert contract.total_amount == Decimal("15000.00")
    assert contract.amount_due == Decimal("10000.00")
    assert contract.signed is False
    assert isinstance(contract.created_at, datetime)


def test_contract_amount_paid_property(sample_contract):
    """Test contract amount_paid computed property"""
    sample_contract.total_amount = Decimal("10000.00")
    sample_contract.amount_due = Decimal("3000.00")

    assert sample_contract.amount_paid == Decimal("7000.00")


def test_contract_sign_method(sample_contract, test_session):
    """Test contract signing"""
    assert sample_contract.signed is False

    sample_contract.sign_contract()
    test_session.commit()

    assert sample_contract.signed is True


def test_contract_update_payment(sample_contract, test_session):
    """Test contract payment update"""
    sample_contract.total_amount = Decimal("10000.00")
    sample_contract.amount_due = Decimal("10000.00")

    # Make a payment
    sample_contract.update_payment(Decimal("4000.00"))
    test_session.commit()

    assert sample_contract.amount_due == Decimal("6000.00")

    # Overpayment should result in 0 due
    sample_contract.update_payment(Decimal("15000.00"))
    assert sample_contract.amount_due == Decimal("0")


def test_contract_relationships(sample_contract, sample_client, test_session):
    """Test contract relationships"""
    test_session.refresh(sample_contract)
    assert sample_contract.client.id == sample_client.id
    assert sample_contract.client.full_name == "John Doe"


def test_contract_repr(sample_contract):
    """Test contract string representation"""
    repr_str = repr(sample_contract)
    assert str(sample_contract.id) in repr_str
    assert str(sample_contract.client_id) in repr_str
    assert "False" in repr_str  # signed status


def test_event_model_creation(test_session, signed_contract):
    """Test event model creation"""
    event = Event(
        name="Product Launch",
        contract_id=signed_contract.id,
        event_date_start=datetime.now() + timedelta(days=7),
        event_date_end=datetime.now() + timedelta(days=8),
        location="Tech Center Paris",
        attendees=200,
        notes="New product launch event",
    )

    test_session.add(event)
    test_session.commit()

    assert event.id is not None
    assert event.name == "Product Launch"
    assert event.attendees == 200
    assert event.support_contact_id is None


def test_event_assign_support(sample_event, support_user, test_session):
    """Test assigning support to event"""
    sample_event.support_contact_id = None
    test_session.commit()

    sample_event.assign_support(support_user.id)
    test_session.commit()

    assert sample_event.support_contact_id == support_user.id


def test_event_client_property(sample_event, sample_client, test_session):
    """Test event client property through contract"""
    test_session.refresh(sample_event)

    client = sample_event.client
    assert client is not None
    assert client.id == sample_client.id
    assert client.full_name == "John Doe"


def test_event_client_contact_property(sample_event, sample_client, test_session):
    """Test event client_contact property"""
    test_session.refresh(sample_event)

    contact_info = sample_event.client_contact
    assert contact_info is not None
    assert "John Doe" in contact_info
    assert "john.doe@example.com" in contact_info
    assert "+33 6 12 34 56 78" in contact_info


def test_event_repr(sample_event):
    """Test event string representation"""
    repr_str = repr(sample_event)
    assert "Annual Conference" in repr_str
    assert str(sample_event.event_date_start) in repr_str


def test_event_without_contract():
    """Test event client property when contract is None"""
    event = Event(
        name="Test Event",
        contract_id=1,
        event_date_start=datetime.now(),
        event_date_end=datetime.now() + timedelta(hours=2),
        location="Test Location",
        attendees=50,
    )
    # Don't set contract relationship

    assert event.client is None
    assert event.client_contact is None


def test_model_datetime_fields(sample_client, sample_contract, sample_event):
    """Test datetime fields in all models"""
    # Client dates
    assert isinstance(sample_client.created_at, datetime)
    assert isinstance(sample_client.updated_at, datetime)

    # Contract date
    assert isinstance(sample_contract.created_at, datetime)

    # Event dates
    assert isinstance(sample_event.event_date_start, datetime)
    assert isinstance(sample_event.event_date_end, datetime)
    assert sample_event.event_date_end > sample_event.event_date_start


def test_decimal_fields_precision(sample_contract):
    """Test decimal field precision in contracts"""
    sample_contract.total_amount = Decimal("12345.67")
    sample_contract.amount_due = Decimal("9876.54")

    assert sample_contract.total_amount == Decimal("12345.67")
    assert sample_contract.amount_due == Decimal("9876.54")
    assert sample_contract.amount_paid == Decimal("2469.13")
