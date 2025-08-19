import click
from rich.console import Console
from rich.table import Table
from getpass import getpass
from ..app.auth import AuthService, Department
from ..app.utils.permissions import get_current_user
from ..app.database import get_session
from sqlmodel import select
from ..app.auth.models import User as UserModel


console = Console()


@click.group()
def user():
    """User management commands (Management only)"""
    pass


@user.command()
def list():
    """List all users"""
    current_user = get_current_user()
    if not current_user:
        console.print("[red]✗[/red] Please login first")
        return

    if not current_user.is_management:
        console.print("[red]✗[/red] Only management can view all users")
        return

    try:
        with get_session() as session:
            users = session.exec(select(UserModel)).all()

            if not users:
                console.print("[yellow]No users found[/yellow]")
                return

            table = Table(title="Users")
            table.add_column("ID", style="cyan")
            table.add_column("Employee ID", style="green")
            table.add_column("Name")
            table.add_column("Email")
            table.add_column("Department", style="yellow")
            table.add_column("Active", style="green")

            for u in users:
                active_status = "✓" if u.is_active else "✗"
                table.add_row(
                    str(u.id),
                    u.employee_id,
                    u.full_name,
                    u.email,
                    u.department.value,
                    active_status,
                )

            console.print(table)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@user.command()
@click.option("--employee-id", prompt=True, help="Employee ID")
@click.option("--full-name", prompt=True, help="Full name")
@click.option("--email", prompt=True, help="Email address")
@click.option(
    "--department",
    prompt=True,
    type=click.Choice(["COMMERCIAL", "SUPPORT", "MANAGEMENT"]),
    help="Department",
)
def create(employee_id: str, full_name: str, email: str, department: str):
    """Create a new user"""
    current_user = get_current_user()
    if not current_user:
        console.print("[red]✗[/red] Please login first")
        return

    if not current_user.is_management:
        console.print("[red]✗[/red] Only management can create users")
        return

    password = getpass("Password: ")
    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        console.print("[red]✗[/red] Passwords do not match")
        return

    try:
        user = AuthService.create_user(
            employee_id=employee_id,
            full_name=full_name,
            email=email,
            password=password,
            department=Department[department],
        )
        console.print(f"[green]✓[/green] User created with ID: {user.id}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@user.command()
@click.argument("user_id", type=int)
@click.option("--full-name", help="New full name")
@click.option("--email", help="New email")
@click.option(
    "--department",
    type=click.Choice(["COMMERCIAL", "SUPPORT", "MANAGEMENT"]),
    help="New department",
)
@click.option("--active/--inactive", default=None, help="User active status")
def update(
    user_id: int,
    full_name: str = None,
    email: str = None,
    department: str = None,
    active: bool = None,
):
    """Update a user"""
    current_user = get_current_user()
    if not current_user:
        console.print("[red]✗[/red] Please login first")
        return

    if not current_user.is_management:
        console.print("[red]✗[/red] Only management can update users")
        return

    try:
        dept = Department[department] if department else None
        updated_user = AuthService.update_user(
            user_id=user_id, full_name=full_name, email=email, department=dept, is_active=active
        )
        console.print(f"[green]✓[/green] User {updated_user.id} updated successfully")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@user.command()
@click.argument("user_id", type=int)
def delete(user_id: int):
    """Delete a user"""
    current_user = get_current_user()
    if not current_user:
        console.print("[red]✗[/red] Please login first")
        return

    if not current_user.is_management:
        console.print("[red]✗[/red] Only management can delete users")
        return

    if current_user.id == user_id:
        console.print("[red]✗[/red] You cannot delete yourself")
        return

    if click.confirm(f"Are you sure you want to delete user {user_id}?"):
        try:
            if AuthService.delete_user(user_id):
                console.print(f"[green]✓[/green] User {user_id} deleted successfully")
            else:
                console.print(f"[red]✗[/red] User {user_id} not found")
        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")


@user.command()
@click.argument("user_id", type=int)
def reset_password(user_id: int):
    """Reset a user's password"""
    current_user = get_current_user()
    if not current_user:
        console.print("[red]✗[/red] Please login first")
        return

    if not current_user.is_management:
        console.print("[red]✗[/red] Only management can reset passwords")
        return

    new_password = getpass("New password: ")
    confirm_password = getpass("Confirm password: ")

    if new_password != confirm_password:
        console.print("[red]✗[/red] Passwords do not match")
        return

    try:
        if AuthService.change_password(user_id, new_password):
            console.print(f"[green]✓[/green] Password reset successfully for user {user_id}")
        else:
            console.print(f"[red]✗[/red] User {user_id} not found")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
