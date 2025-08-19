import click
from rich.console import Console
from rich.table import Table
from ..app.database import init_database
from ..app.utils import init_sentry
from .auth_commands import auth
from .client_commands import client
from .contract_commands import contract
from .event_commands import event
from .user_commands import user


console = Console()


init_sentry()


@click.group()
@click.version_option(version="1.0.0", prog_name="Epic Events CRM")
def cli():
    """Epic Events CRM - Customer Relationship Management System"""
    pass


@cli.command()
def init():
    """Initialize the database"""
    try:
        init_database()
        console.print("[green]✓[/green] Database initialized successfully!")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to initialize database: {e}")
        raise click.Abort()


cli.add_command(auth)
cli.add_command(client)
cli.add_command(contract)
cli.add_command(event)
cli.add_command(user)


if __name__ == "__main__":
    cli()
