"""
Integration tests for database operations
"""

import pytest
from sqlmodel import select
from datetime import datetime, timedelta
from decimal import Decimal
from epicevents.app.models import Client, Contract, Event
from epicevents.app.auth.models import User, Department
from epicevents.app.database import create_db_and_tables, get_session


def test_database_initialization(test_db):
    """Test database tables are created correctly"""
    # Tables should be created by the fixture
    from sqlmodel import inspect

    inspector = inspect(test_db)
    tables = inspector.get_table_names()

    assert "users" in tables
    assert "clients" in tables
    assert "contracts" in tables
    assert "events" in tables


def test_cascade_relationships(test_session, commercial_user):
    """Test cascade behaviors between related entities"""
    # Create client with commercial
    client = Client(
        full_name="Cascade Test Client",
        email="cascade@test.com",
        phone="+33611111111",
        company_name="Cascade Corp",
        commercial_id=commercial_user.id,
    )
    test_session.add(client)
    test_session.commit()

    # Create contract
    contract = Contract(
        client_id=client.id,
        commercial_id=commercial_user.id,
        total_amount=Decimal("10000.00"),
        amount_due=Decimal("10000.00"),
        signed=True,
    )
    test_session.add(contract)
    test_session.commit()

    # Create event
    event = Event(
        name="Cascade Event",
        contract_id=contract.id,
        event_date_start=datetime.now() + timedelta(days=10),
        event_date_end=datetime.now() + timedelta(days=11),
        location="Cascade Location",
        attendees=50,
    )
    test_session.add(event)
    test_session.commit()

    # Test relationships are properly loaded
    test_session.refresh(client)
    assert len(client.contracts) == 1

    test_session.refresh(contract)
    assert contract.client.id == client.id
    assert len(contract.events) == 1

    test_session.refresh(event)
    assert event.contract.id == contract.id


def test_transaction_rollback(test_session):
    """Test transaction rollback on error"""
    initial_count = test_session.exec(select(Client)).all()

    try:
        # Create a client
        client = Client(
            full_name="Rollback Test",
            email="rollback@test.com",
            phone="+33622222222",
            company_name="Rollback Corp",
        )
        test_session.add(client)

        # Force an error (duplicate email)
        duplicate = Client(
            full_name="Duplicate",
            email="rollback@test.com",  # Same email
            phone="+33633333333",
            company_name="Duplicate Corp",
        )
        test_session.add(duplicate)
        test_session.commit()

    except Exception:
        test_session.rollback()

    # Verify no clients were added
    final_count = test_session.exec(select(Client)).all()
    assert len(final_count) == len(initial_count)


def test_concurrent_updates(test_session, sample_client):
    """Test handling concurrent updates to same entity"""
    # Simulate two users updating same client
    original_name = sample_client.full_name
    original_phone = sample_client.phone

    # First update
    sample_client.full_name = "First Update"
    test_session.add(sample_client)
    test_session.commit()

    # Second update
    sample_client.phone = "+33699999999"
    test_session.add(sample_client)
    test_session.commit()

    # Verify both updates are applied
    test_session.refresh(sample_client)
    assert sample_client.full_name == "First Update"
    assert sample_client.phone == "+33699999999"


def test_large_dataset_pagination(test_session, commercial_user):
    """Test handling large datasets with pagination"""
    # Create many clients
    for i in range(50):
        client = Client(
            full_name=f"Client {i:03d}",
            email=f"client{i:03d}@test.com",
            phone=f"+336{i:08d}",
            company_name=f"Company {i:03d}",
            commercial_id=commercial_user.id,
        )
        test_session.add(client)
    test_session.commit()

    # Test pagination
    page_size = 10
    offset = 0

    page1 = test_session.exec(select(Client).offset(offset).limit(page_size)).all()
    assert len(page1) == page_size

    offset = 20
    page3 = test_session.exec(select(Client).offset(offset).limit(page_size)).all()
    assert len(page3) == page_size

    # Verify different pages have different data
    page1_ids = {c.id for c in page1}
    page3_ids = {c.id for c in page3}
    assert page1_ids.isdisjoint(page3_ids)


def test_complex_queries(test_session, commercial_user, support_user):
    """Test complex database queries with joins and filters"""
    # Create test data
    client1 = Client(
        full_name="Premium Client",
        email="premium@test.com",
        phone="+33611111111",
        company_name="Premium Corp",
        commercial_id=commercial_user.id,
    )
    client2 = Client(
        full_name="Standard Client",
        email="standard@test.com",
        phone="+33622222222",
        company_name="Standard Corp",
        commercial_id=commercial_user.id,
    )
    test_session.add_all([client1, client2])
    test_session.commit()

    # Create contracts with different amounts
    contract1 = Contract(
        client_id=client1.id,
        commercial_id=commercial_user.id,
        total_amount=Decimal("100000.00"),
        amount_due=Decimal("50000.00"),
        signed=True,
    )
    contract2 = Contract(
        client_id=client2.id,
        commercial_id=commercial_user.id,
        total_amount=Decimal("20000.00"),
        amount_due=Decimal("0.00"),
        signed=True,
    )
    test_session.add_all([contract1, contract2])
    test_session.commit()

    # Create events
    event1 = Event(
        name="Premium Event",
        contract_id=contract1.id,
        event_date_start=datetime.now() + timedelta(days=30),
        event_date_end=datetime.now() + timedelta(days=31),
        location="Premium Location",
        attendees=500,
        support_contact_id=support_user.id,
    )
    event2 = Event(
        name="Standard Event",
        contract_id=contract2.id,
        event_date_start=datetime.now() + timedelta(days=60),
        event_date_end=datetime.now() + timedelta(days=61),
        location="Standard Location",
        attendees=100,
        support_contact_id=None,
    )
    test_session.add_all([event1, event2])
    test_session.commit()

    # Complex query: Find high-value contracts with events needing support
    from sqlmodel import and_, or_

    high_value_unpaid = test_session.exec(
        select(Contract).where(and_(Contract.total_amount > 50000, Contract.amount_due > 0))
    ).all()

    assert len(high_value_unpaid) >= 1
    assert all(c.total_amount > 50000 and c.amount_due > 0 for c in high_value_unpaid)

    # Find events without support
    no_support_events = test_session.exec(
        select(Event).where(Event.support_contact_id == None)
    ).all()

    assert len(no_support_events) >= 1
    assert all(e.support_contact_id is None for e in no_support_events)

    # Join query: Clients with unsigned contracts
    unsigned_contract_clients = test_session.exec(
        select(Client).join(Contract).where(Contract.signed == False)
    ).all()

    # Aggregate query: Total revenue per commercial
    from sqlmodel import func

    revenue_query = select(
        Contract.commercial_id, func.sum(Contract.total_amount).label("total_revenue")
    ).group_by(Contract.commercial_id)

    results = test_session.exec(revenue_query).all()
    assert len(results) >= 1


def test_database_constraints(test_session):
    """Test database constraints are enforced"""
    # Test unique constraint on email
    client1 = Client(
        full_name="Client One",
        email="unique@test.com",
        phone="+33611111111",
        company_name="Company One",
    )
    test_session.add(client1)
    test_session.commit()

    client2 = Client(
        full_name="Client Two",
        email="unique@test.com",  # Duplicate email
        phone="+33622222222",
        company_name="Company Two",
    )
    test_session.add(client2)

    with pytest.raises(Exception):  # Should raise integrity error
        test_session.commit()

    test_session.rollback()

    # Test foreign key constraint
    with pytest.raises(Exception):
        invalid_contract = Contract(
            client_id=99999,  # Non-existent client
            total_amount=Decimal("10000.00"),
            amount_due=Decimal("10000.00"),
            signed=False,
        )
        test_session.add(invalid_contract)
        test_session.commit()

    test_session.rollback()


def test_datetime_handling(test_session, signed_contract):
    """Test datetime field handling across different operations"""
    # Create event with specific times
    start_time = datetime(2024, 12, 25, 14, 0, 0)
    end_time = datetime(2024, 12, 26, 2, 0, 0)

    event = Event(
        name="Christmas Event",
        contract_id=signed_contract.id,
        event_date_start=start_time,
        event_date_end=end_time,
        location="Christmas Location",
        attendees=150,
    )
    test_session.add(event)
    test_session.commit()

    # Retrieve and verify
    test_session.refresh(event)
    assert event.event_date_start == start_time
    assert event.event_date_end == end_time
    assert event.event_date_end > event.event_date_start

    # Test date filtering
    future_events = test_session.exec(
        select(Event).where(Event.event_date_start > datetime.now())
    ).all()

    past_events = test_session.exec(
        select(Event).where(Event.event_date_end < datetime.now())
    ).all()

    # At least our Christmas event should be in appropriate list
    if start_time > datetime.now():
        assert any(e.name == "Christmas Event" for e in future_events)


def test_decimal_precision(test_session, sample_client, commercial_user):
    """Test decimal field precision for monetary values"""
    # Test various decimal values
    test_values = [Decimal("0.01"), Decimal("999.99"), Decimal("12345.67"), Decimal("99999999.99")]

    contracts = []
    for i, amount in enumerate(test_values):
        contract = Contract(
            client_id=sample_client.id,
            commercial_id=commercial_user.id,
            total_amount=amount,
            amount_due=amount / 2,
            signed=False,
        )
        test_session.add(contract)
        contracts.append(contract)

    test_session.commit()

    # Verify precision is maintained
    for contract, original_amount in zip(contracts, test_values):
        test_session.refresh(contract)
        assert contract.total_amount == original_amount
        assert contract.amount_due == original_amount / 2
