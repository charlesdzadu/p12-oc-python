#!/usr/bin/env python
"""
Database initialization script for Epic Events CRM.
Creates tables and initial data.
"""

import sys
from pathlib import Path
from getpass import getpass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from epicevents.app.database import create_db_and_tables, get_session
from epicevents.app.auth import AuthService, Department
from epicevents.app.auth.models import User
from sqlmodel import select
from rich.console import Console
from rich.prompt import Prompt, Confirm


console = Console()


def create_initial_admin():
    """Create the initial admin user if no users exist"""
    with get_session() as session:
        existing_users = session.exec(select(User)).all()

        if existing_users:
            console.print(
                "[yellow]Users already exist in the database. Skipping admin creation.[/yellow]"
            )
            return

        console.print("[cyan]Creating initial admin user...[/cyan]")

        employee_id = Prompt.ask("Admin Employee ID", default="ADM001")
        full_name = Prompt.ask("Admin Full Name", default="Administrator")
        email = Prompt.ask("Admin Email")
        password = getpass("Admin Password: ")
        confirm_password = getpass("Confirm Password: ")

        if password != confirm_password:
            console.print("[red]✗[/red] Passwords do not match!")
            sys.exit(1)

        try:
            admin = AuthService.create_user(
                employee_id=employee_id,
                full_name=full_name,
                email=email,
                password=password,
                department=Department.MANAGEMENT,
            )

            console.print(f"[green]✓[/green] Admin user created successfully!")
            console.print(f"  Email: {email}")
            console.print(f"  Department: {Department.MANAGEMENT.value}")
            console.print(f"  Employee ID: {employee_id}")

        except Exception as e:
            console.print(f"[red]✗[/red] Failed to create admin user: {e}")
            sys.exit(1)


def init_database():
    """Initialize the database with tables and initial data"""
    console.print("[cyan]Initializing Epic Events CRM Database...[/cyan]")

    try:
        console.print("Creating database tables...")
        create_db_and_tables()
        console.print("[green]✓[/green] Database tables created successfully!")

        if Confirm.ask("Do you want to create an initial admin user?", default=True):
            create_initial_admin()

        console.print("\n[green]✓[/green] Database initialization complete!")
        console.print("\n[cyan]You can now use the CRM with:[/cyan]")
        console.print("  poetry run epicevents auth login")

    except Exception as e:
        console.print(f"[red]✗[/red] Database initialization failed: {e}")
        sys.exit(1)


def create_sample_data():
    """Create sample data for testing (optional)"""
    from epicevents.app.services import ClientService, ContractService, EventService
    from datetime import datetime, timedelta
    from decimal import Decimal

    console.print("[cyan]Creating sample data...[/cyan]")

    with get_session() as session:
        management_user = session.exec(
            select(User).where(User.department == Department.MANAGEMENT)
        ).first()

        if not management_user:
            console.print("[red]✗[/red] No management user found. Please create one first.")
            return

        try:
            commercial = AuthService.create_user(
                employee_id="COM001",
                full_name="Jean Commercial",
                email="jean.commercial@epicevents.com",
                password="password123",
                department=Department.COMMERCIAL,
            )
            console.print(f"[green]✓[/green] Created commercial user: {commercial.email}")

            support = AuthService.create_user(
                employee_id="SUP001",
                full_name="Marie Support",
                email="marie.support@epicevents.com",
                password="password123",
                department=Department.SUPPORT,
            )
            console.print(f"[green]✓[/green] Created support user: {support.email}")

            client = ClientService.create_client(
                full_name="John Doe",
                email="john.doe@example.com",
                phone="+33 6 12 34 56 78",
                company_name="Example Corp",
                commercial_id=commercial.id,
                current_user=commercial,
            )
            console.print(f"[green]✓[/green] Created client: {client.full_name}")

            contract = ContractService.create_contract(
                client_id=client.id,
                total_amount=Decimal("10000.00"),
                amount_due=Decimal("5000.00"),
                commercial_id=commercial.id,
                current_user=management_user,
            )
            console.print(f"[green]✓[/green] Created contract: ID {contract.id}")

            contract = ContractService.sign_contract(contract.id, commercial)
            console.print(f"[green]✓[/green] Signed contract: ID {contract.id}")

            event = EventService.create_event(
                name="Annual Conference",
                contract_id=contract.id,
                event_date_start=datetime.now() + timedelta(days=30),
                event_date_end=datetime.now() + timedelta(days=31),
                location="Paris Convention Center",
                attendees=150,
                notes="Annual company conference with keynote speakers",
                current_user=commercial,
            )
            console.print(f"[green]✓[/green] Created event: {event.name}")

            event = EventService.assign_support_contact(
                event_id=event.id, support_contact_id=support.id, current_user=management_user
            )
            console.print(f"[green]✓[/green] Assigned support to event")

            console.print("\n[green]✓[/green] Sample data created successfully!")
            console.print("\n[cyan]Test credentials:[/cyan]")
            console.print("  Commercial: jean.commercial@epicevents.com / password123")
            console.print("  Support: marie.support@epicevents.com / password123")

        except Exception as e:
            console.print(f"[yellow]Sample data creation partially failed: {e}[/yellow]")


if __name__ == "__main__":
    init_database()

    if "--sample-data" in sys.argv:
        create_sample_data()
