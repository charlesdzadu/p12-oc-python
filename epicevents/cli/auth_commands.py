import click
from rich.console import Console
from rich.prompt import Prompt
from getpass import getpass
from ..app.auth import AuthService, save_token, load_token, remove_token


console = Console()


@click.group()
def auth():
    """Authentication commands"""
    pass


@auth.command()
@click.option("--email", prompt=True, help="Your email address")
def login(email: str):
    """Login to the system"""
    password = getpass("Password: ")

    try:
        token = AuthService.authenticate(email, password)
        if token:
            save_token(token)
            # Decode token to get user info without accessing the database
            from ..app.auth.utils import decode_access_token
            payload = decode_access_token(token)
            console.print(f"[green]✓[/green] Welcome! You are now logged in.")
            console.print(f"Email: {payload['email']}")
            console.print(f"Department: {payload['department']}")
        else:
            console.print("[red]✗[/red] Invalid email or password")
    except Exception as e:
        console.print(f"[red]✗[/red] Login failed: {e}")


@auth.command()
def logout():
    """Logout from the system"""
    remove_token()
    console.print("[green]✓[/green] Logged out successfully")


@auth.command()
def whoami():
    """Show current logged-in user"""
    from ..app.auth.utils import load_token, decode_access_token
    token = load_token()
    if token:
        payload = decode_access_token(token)
        if payload:
            console.print(f"[cyan]Email:[/cyan] {payload['email']}")
            console.print(f"[cyan]Employee ID:[/cyan] {payload['employee_id']}")
            console.print(f"[cyan]Department:[/cyan] {payload['department']}")
        else:
            console.print("[yellow]Invalid or expired token[/yellow]")
    else:
        console.print("[yellow]Not logged in[/yellow]")
