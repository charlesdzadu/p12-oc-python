import click
from rich.console import Console
from rich.table import Table
from ..app.services import ClientService
from ..app.utils.permissions import get_current_user
from ..app.database import get_session
from ..app.repositories.client_repo import ClientRepository


console = Console()


@click.group()
def client():
    """Client management commands"""
    pass


@client.command()
@click.option("--filter-commercial", type=int, help="Filter by commercial ID")
def list(filter_commercial: int = None):
    """List all clients"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        if not user.has_permission("read", "client"):
            console.print("[red]✗[/red] You don't have permission to view clients")
            return

        with get_session() as session:
            repo = ClientRepository(session)
            
            if filter_commercial:
                clients = repo.get_by_commercial(filter_commercial)
            elif user.is_commercial:
                clients = repo.get_by_commercial(user.id)
            else:
                clients = repo.get_all()

            if not clients:
                console.print("[yellow]No clients found[/yellow]")
                return

            table = Table(title="Clients")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Email")
            table.add_column("Phone")
            table.add_column("Company")
            table.add_column("Commercial", style="yellow")

            for c in clients:
                commercial_name = c.commercial.full_name if c.commercial else "Unassigned"
                table.add_row(str(c.id), c.full_name, c.email, c.phone, c.company_name, commercial_name)

            console.print(table)
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@client.command()
@click.option("--full-name", prompt=True, help="Client full name")
@click.option("--email", prompt=True, help="Client email")
@click.option("--phone", prompt=True, help="Client phone")
@click.option("--company", prompt=True, help="Company name")
def create(full_name: str, email: str, phone: str, company: str):
    """Create a new client"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        client = ClientService.create_client(
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company,
            commercial_id=user.id,
            current_user=user,
        )
        console.print(f"[green]✓[/green] Client created with ID: {client.id}")
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@client.command()
@click.argument("client_id", type=int)
@click.option("--full-name", help="New full name")
@click.option("--email", help="New email")
@click.option("--phone", help="New phone")
@click.option("--company", help="New company name")
def update(
    client_id: int, full_name: str = None, email: str = None, phone: str = None, company: str = None
):
    """Update a client"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        updated_client = ClientService.update_client(
            client_id=client_id,
            current_user=user,
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company,
        )
        console.print(f"[green]✓[/green] Client {updated_client.id} updated successfully")
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@client.command()
@click.argument("query")
def search(query: str):
    """Search clients by name or company"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        if not user.has_permission("read", "client"):
            console.print("[red]✗[/red] You don't have permission to search clients")
            return

        with get_session() as session:
            repo = ClientRepository(session)
            clients = repo.search_by_name(query)

            if not clients:
                console.print(f"[yellow]No clients found matching '{query}'[/yellow]")
                return

            table = Table(title=f"Search Results for '{query}'")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Email")
            table.add_column("Company")
            table.add_column("Commercial", style="yellow")

            for c in clients:
                commercial_name = c.commercial.full_name if c.commercial else "Unassigned"
                table.add_row(str(c.id), c.full_name, c.email, c.company_name, commercial_name)

            console.print(table)
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
