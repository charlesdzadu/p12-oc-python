"""
Shared fixtures for all tests
"""

import pytest
import tempfile
import os
from pathlib import Path
from sqlmodel import Session, create_engine, SQLModel
from click.testing import CliRunner
from decimal import Decimal
from datetime import datetime, timedelta

from epicevents.app.auth.models import User, Department
from epicevents.app.models import Client, Contract, Event
from epicevents.app.auth.service import AuthService
from epicevents.app.auth.utils import hash_password


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        test_db_path = f.name

    test_engine = create_engine(f"sqlite:///{test_db_path}")
    SQLModel.metadata.create_all(test_engine)

    yield test_engine

    # Cleanup
    os.unlink(test_db_path)


@pytest.fixture
def test_session(test_db):
    """Create a test database session"""
    with Session(test_db) as session:
        yield session


@pytest.fixture
def mock_get_session(test_session):
    """Mock the get_session function to use test session"""
    from contextlib import contextmanager

    @contextmanager
    def _get_session():
        yield test_session

    return _get_session


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner"""
    return CliRunner()


@pytest.fixture
def temp_token_file():
    """Create a temporary token file"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
        token_path = Path(f.name)

    yield token_path

    # Cleanup
    if token_path.exists():
        token_path.unlink()


@pytest.fixture
def management_user(test_session):
    """Create a management department user"""
    user = User(
        employee_id="MGT001",
        full_name="Test Manager",
        email="manager@test.com",
        password_hash=hash_password("password123"),
        department=Department.MANAGEMENT,
        is_active=True,
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def commercial_user(test_session):
    """Create a commercial department user"""
    user = User(
        employee_id="COM001",
        full_name="Test Commercial",
        email="commercial@test.com",
        password_hash=hash_password("password123"),
        department=Department.COMMERCIAL,
        is_active=True,
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def support_user(test_session):
    """Create a support department user"""
    user = User(
        employee_id="SUP001",
        full_name="Test Support",
        email="support@test.com",
        password_hash=hash_password("password123"),
        department=Department.SUPPORT,
        is_active=True,
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def sample_client(test_session, commercial_user):
    """Create a sample client"""
    client = Client(
        full_name="John Doe",
        email="john.doe@example.com",
        phone="+33 6 12 34 56 78",
        company_name="Example Corp",
        commercial_id=commercial_user.id,
    )
    test_session.add(client)
    test_session.commit()
    test_session.refresh(client)
    return client


@pytest.fixture
def sample_contract(test_session, sample_client, commercial_user):
    """Create a sample contract"""
    contract = Contract(
        client_id=sample_client.id,
        commercial_id=commercial_user.id,
        total_amount=Decimal("10000.00"),
        amount_due=Decimal("5000.00"),
        signed=False,
    )
    test_session.add(contract)
    test_session.commit()
    test_session.refresh(contract)
    return contract


@pytest.fixture
def signed_contract(test_session, sample_contract):
    """Create a signed contract"""
    sample_contract.signed = True
    test_session.add(sample_contract)
    test_session.commit()
    test_session.refresh(sample_contract)
    return sample_contract


@pytest.fixture
def sample_event(test_session, signed_contract, support_user):
    """Create a sample event"""
    event = Event(
        name="Annual Conference",
        contract_id=signed_contract.id,
        event_date_start=datetime.now() + timedelta(days=30),
        event_date_end=datetime.now() + timedelta(days=31),
        location="Paris Convention Center",
        attendees=150,
        notes="Annual company conference",
        support_contact_id=support_user.id,
    )
    test_session.add(event)
    test_session.commit()
    test_session.refresh(event)
    return event


@pytest.fixture
def auth_token(commercial_user):
    """Create an authentication token"""
    from epicevents.app.auth.utils import create_access_token

    token_data = {
        "user_id": commercial_user.id,
        "email": commercial_user.email,
        "department": commercial_user.department.value,
        "employee_id": commercial_user.employee_id,
    }
    return create_access_token(token_data)


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    """Setup test environment variables"""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_EXPIRATION_HOURS", "24")
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DEBUG", "false")
