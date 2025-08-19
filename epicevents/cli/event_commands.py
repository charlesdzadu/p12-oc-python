import click
from rich.console import Console
from rich.table import Table
from datetime import datetime
from ..app.services import EventService
from ..app.utils.permissions import get_current_user


console = Console()


@click.group()
def event():
    """Event management commands"""
    pass


@event.command()
@click.option("--without-support", is_flag=True, help="Show only events without support")
@click.option("--upcoming", is_flag=True, help="Show only upcoming events")
@click.option("--past", is_flag=True, help="Show only past events")
@click.option("--contract-id", type=int, help="Filter by contract ID")
def list(without_support: bool, upcoming: bool, past: bool, contract_id: int = None):
    """List events"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        events = EventService.list_events(
            user,
            without_support=without_support,
            upcoming_only=upcoming,
            past_only=past,
            contract_id=contract_id,
        )

        if not events:
            console.print("[yellow]No events found[/yellow]")
            return

        table = Table(title="Events")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Start Date")
        table.add_column("End Date")
        table.add_column("Location")
        table.add_column("Attendees")
        table.add_column("Support", style="yellow")

        for e in events:
            support_name = e.support_contact.full_name if e.support_contact else "Unassigned"

            table.add_row(
                str(e.id),
                e.name,
                e.event_date_start.strftime("%Y-%m-%d %H:%M"),
                e.event_date_end.strftime("%Y-%m-%d %H:%M"),
                e.location[:30] + "..." if len(e.location) > 30 else e.location,
                str(e.attendees),
                support_name,
            )

        console.print(table)
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@event.command()
@click.option("--name", prompt=True, help="Event name")
@click.option("--contract-id", prompt=True, type=int, help="Contract ID")
@click.option("--start", prompt=True, help="Start date (YYYY-MM-DD HH:MM)")
@click.option("--end", prompt=True, help="End date (YYYY-MM-DD HH:MM)")
@click.option("--location", prompt=True, help="Event location")
@click.option("--attendees", prompt=True, type=int, help="Number of attendees")
@click.option("--notes", help="Event notes")
def create(
    name: str,
    contract_id: int,
    start: str,
    end: str,
    location: str,
    attendees: int,
    notes: str = None,
):
    """Create a new event"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        start_date = datetime.strptime(start, "%Y-%m-%d %H:%M")
        end_date = datetime.strptime(end, "%Y-%m-%d %H:%M")

        event = EventService.create_event(
            name=name,
            contract_id=contract_id,
            event_date_start=start_date,
            event_date_end=end_date,
            location=location,
            attendees=attendees,
            notes=notes,
            current_user=user,
        )
        console.print(f"[green]✓[/green] Event created with ID: {event.id}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@event.command()
@click.argument("event_id", type=int)
@click.option("--name", help="New event name")
@click.option("--start", help="New start date (YYYY-MM-DD HH:MM)")
@click.option("--end", help="New end date (YYYY-MM-DD HH:MM)")
@click.option("--location", help="New location")
@click.option("--attendees", type=int, help="New number of attendees")
@click.option("--notes", help="New notes")
def update(
    event_id: int,
    name: str = None,
    start: str = None,
    end: str = None,
    location: str = None,
    attendees: int = None,
    notes: str = None,
):
    """Update an event"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        start_date = datetime.strptime(start, "%Y-%m-%d %H:%M") if start else None
        end_date = datetime.strptime(end, "%Y-%m-%d %H:%M") if end else None

        updated_event = EventService.update_event(
            event_id=event_id,
            current_user=user,
            name=name,
            event_date_start=start_date,
            event_date_end=end_date,
            location=location,
            attendees=attendees,
            notes=notes,
        )
        console.print(f"[green]✓[/green] Event {updated_event.id} updated successfully")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@event.command()
@click.argument("event_id", type=int)
@click.option("--support-id", prompt=True, type=int, help="Support user ID")
def assign_support(event_id: int, support_id: int):
    """Assign support contact to an event"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        event = EventService.assign_support_contact(event_id, support_id, user)
        console.print(f"[green]✓[/green] Support contact assigned to event {event.id}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@event.command()
@click.argument("location")
def search(location: str):
    """Search events by location"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        events = EventService.search_events_by_location(location, user)

        if not events:
            console.print(f"[yellow]No events found at location '{location}'[/yellow]")
            return

        table = Table(title=f"Events at '{location}'")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Date")
        table.add_column("Location")

        for e in events:
            table.add_row(
                str(e.id),
                e.name,
                e.event_date_start.strftime("%Y-%m-%d"),
                e.location[:40] + "..." if len(e.location) > 40 else e.location,
            )

        console.print(table)
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
