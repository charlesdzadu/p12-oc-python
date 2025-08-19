"""
Integration tests for complete workflows
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from epicevents.app.auth.service import AuthService
from epicevents.app.services import ClientService, ContractService, EventService
from epicevents.app.auth.models import Department


def test_complete_client_to_event_workflow(test_session, mock_get_session, monkeypatch):
    """Test complete workflow from user creation to event management"""
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.services.client_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.services.contract_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)

    # Step 1: Create users
    management = AuthService.create_user(
        employee_id="MGT001",
        full_name="Manager User",
        email="manager@workflow.com",
        password="password123",
        department=Department.MANAGEMENT,
    )

    commercial = AuthService.create_user(
        employee_id="COM001",
        full_name="Commercial User",
        email="commercial@workflow.com",
        password="password123",
        department=Department.COMMERCIAL,
    )

    support = AuthService.create_user(
        employee_id="SUP001",
        full_name="Support User",
        email="support@workflow.com",
        password="password123",
        department=Department.SUPPORT,
    )

    # Step 2: Commercial creates a client
    client = ClientService.create_client(
        full_name="Workflow Client",
        email="client@workflow.com",
        phone="+33611111111",
        company_name="Workflow Corp",
        commercial_id=commercial.id,
        current_user=commercial,
    )

    assert client.id is not None
    assert client.commercial_id == commercial.id

    # Step 3: Management creates a contract
    contract = ContractService.create_contract(
        client_id=client.id,
        total_amount=Decimal("50000.00"),
        amount_due=Decimal("50000.00"),
        commercial_id=commercial.id,
        current_user=management,
    )

    assert contract.id is not None
    assert contract.signed is False

    # Step 4: Commercial signs the contract
    signed_contract = ContractService.sign_contract(contract.id, commercial)
    assert signed_contract.signed is True

    # Step 5: Commercial creates an event
    event = EventService.create_event(
        name="Workflow Event",
        contract_id=signed_contract.id,
        event_date_start=datetime.now() + timedelta(days=30),
        event_date_end=datetime.now() + timedelta(days=31),
        location="Workflow Location",
        attendees=200,
        notes="Complete workflow test",
        current_user=commercial,
    )

    assert event.id is not None
    assert event.support_contact_id is None

    # Step 6: Management assigns support to event
    with monkeypatch.context() as m:
        m.setattr("epicevents.app.auth.service.AuthService.get_current_user", lambda x: support)

        assigned_event = EventService.assign_support_contact(
            event_id=event.id, support_contact_id=support.id, current_user=management
        )

        assert assigned_event.support_contact_id == support.id

    # Step 7: Support updates the event
    updated_event = EventService.update_event(
        event_id=event.id, current_user=support, attendees=250, notes="Updated by support team"
    )

    assert updated_event.attendees == 250
    assert "Updated by support" in updated_event.notes

    # Step 8: Commercial updates payment
    updated_contract = ContractService.update_payment(contract.id, Decimal("20000.00"), commercial)

    assert updated_contract.amount_due == Decimal("30000.00")


def test_department_based_workflow_restrictions(test_session, mock_get_session, monkeypatch):
    """Test that department restrictions are enforced throughout workflow"""
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.services.client_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.services.contract_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)

    # Create users
    commercial = AuthService.create_user(
        employee_id="COM002",
        full_name="Commercial Two",
        email="commercial2@test.com",
        password="password123",
        department=Department.COMMERCIAL,
    )

    support = AuthService.create_user(
        employee_id="SUP002",
        full_name="Support Two",
        email="support2@test.com",
        password="password123",
        department=Department.SUPPORT,
    )

    # Support cannot create clients
    with pytest.raises(PermissionError):
        ClientService.create_client(
            full_name="Invalid Client",
            email="invalid@test.com",
            phone="+33622222222",
            company_name="Invalid Corp",
            commercial_id=support.id,
            current_user=support,
        )

    # Commercial cannot create contracts
    client = ClientService.create_client(
        full_name="Valid Client",
        email="valid@test.com",
        phone="+33633333333",
        company_name="Valid Corp",
        commercial_id=commercial.id,
        current_user=commercial,
    )

    with pytest.raises(PermissionError):
        ContractService.create_contract(
            client_id=client.id,
            total_amount=Decimal("10000.00"),
            amount_due=Decimal("10000.00"),
            commercial_id=commercial.id,
            current_user=commercial,
        )

    # Support cannot create events
    management = AuthService.create_user(
        employee_id="MGT002",
        full_name="Manager Two",
        email="manager2@test.com",
        password="password123",
        department=Department.MANAGEMENT,
    )

    contract = ContractService.create_contract(
        client_id=client.id,
        total_amount=Decimal("10000.00"),
        amount_due=Decimal("10000.00"),
        commercial_id=commercial.id,
        current_user=management,
    )

    signed = ContractService.sign_contract(contract.id, commercial)

    with pytest.raises(PermissionError):
        EventService.create_event(
            name="Invalid Event",
            contract_id=signed.id,
            event_date_start=datetime.now() + timedelta(days=10),
            event_date_end=datetime.now() + timedelta(days=11),
            location="Invalid Location",
            attendees=50,
            notes=None,
            current_user=support,
        )


def test_multiple_clients_contracts_events_workflow(test_session, mock_get_session, monkeypatch):
    """Test workflow with multiple entities and relationships"""
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.services.client_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.services.contract_service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.services.event_service.get_session", mock_get_session)

    # Create users
    commercial1 = AuthService.create_user(
        employee_id="COM003",
        full_name="Commercial Three",
        email="commercial3@test.com",
        password="password123",
        department=Department.COMMERCIAL,
    )

    commercial2 = AuthService.create_user(
        employee_id="COM004",
        full_name="Commercial Four",
        email="commercial4@test.com",
        password="password123",
        department=Department.COMMERCIAL,
    )

    management = AuthService.create_user(
        employee_id="MGT003",
        full_name="Manager Three",
        email="manager3@test.com",
        password="password123",
        department=Department.MANAGEMENT,
    )

    # Each commercial creates clients
    clients_com1 = []
    for i in range(3):
        client = ClientService.create_client(
            full_name=f"Client {i} for Com1",
            email=f"client{i}com1@test.com",
            phone=f"+3361111{i:04d}",
            company_name=f"Company {i} Com1",
            commercial_id=commercial1.id,
            current_user=commercial1,
        )
        clients_com1.append(client)

    clients_com2 = []
    for i in range(2):
        client = ClientService.create_client(
            full_name=f"Client {i} for Com2",
            email=f"client{i}com2@test.com",
            phone=f"+3362222{i:04d}",
            company_name=f"Company {i} Com2",
            commercial_id=commercial2.id,
            current_user=commercial2,
        )
        clients_com2.append(client)

    # Verify commercials can only see their own clients
    com1_clients = ClientService.list_clients(commercial1)
    assert len([c for c in com1_clients if c.commercial_id == commercial1.id]) == 3

    com2_clients = ClientService.list_clients(commercial2)
    assert len([c for c in com2_clients if c.commercial_id == commercial2.id]) == 2

    # Management can see all clients
    all_clients = ClientService.list_clients(management)
    assert len(all_clients) >= 5

    # Create contracts for some clients
    contracts = []
    for client in clients_com1[:2]:
        contract = ContractService.create_contract(
            client_id=client.id,
            total_amount=Decimal("25000.00"),
            amount_due=Decimal("25000.00"),
            commercial_id=commercial1.id,
            current_user=management,
        )
        contracts.append(contract)

    # Sign one contract and create event
    signed = ContractService.sign_contract(contracts[0].id, commercial1)

    event = EventService.create_event(
        name="Multi-workflow Event",
        contract_id=signed.id,
        event_date_start=datetime.now() + timedelta(days=15),
        event_date_end=datetime.now() + timedelta(days=16),
        location="Multi Location",
        attendees=100,
        notes="Multi-entity test",
        current_user=commercial1,
    )

    # Verify relationships
    test_session.refresh(clients_com1[0])
    assert len(clients_com1[0].contracts) >= 1

    # Test filtering
    unsigned = ContractService.list_contracts(management, unsigned_only=True)
    assert any(c.id == contracts[1].id for c in unsigned)

    signed_contracts = ContractService.list_contracts(management, unsigned_only=False)
    assert any(c.signed for c in signed_contracts)


def test_authentication_workflow(test_session, mock_get_session, monkeypatch, temp_token_file):
    """Test authentication workflow"""
    monkeypatch.setattr("epicevents.app.auth.service.get_session", mock_get_session)
    monkeypatch.setattr("epicevents.app.config.TOKEN_FILE", temp_token_file)

    # Create user
    user = AuthService.create_user(
        employee_id="AUTH001",
        full_name="Auth User",
        email="auth@workflow.com",
        password="password123",
        department=Department.COMMERCIAL,
    )

    # Authenticate
    token = AuthService.authenticate("auth@workflow.com", "password123")
    assert token is not None

    # Get current user from token
    from epicevents.app.auth.utils import save_token, load_token

    save_token(token)
    loaded = load_token()
    assert loaded == token

    # Use token to get user
    current = AuthService.get_current_user(token)
    assert current.id == user.id

    # Invalid authentication
    invalid = AuthService.authenticate("auth@workflow.com", "wrongpassword")
    assert invalid is None

    # Update user
    updated = AuthService.update_user(
        user.id, full_name="Updated Auth User", department=Department.SUPPORT
    )
    assert updated.full_name == "Updated Auth User"
    assert updated.department == Department.SUPPORT

    # Change password
    result = AuthService.change_password(user.id, "newpassword123")
    assert result is True

    # Authenticate with new password
    new_token = AuthService.authenticate("auth@workflow.com", "newpassword123")
    assert new_token is not None
