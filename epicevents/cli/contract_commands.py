import click
from rich.console import Console
from rich.table import Table
from decimal import Decimal
from ..app.services import ContractService
from ..app.utils.permissions import get_current_user


console = Console()


@click.group()
def contract():
    """Contract management commands"""
    pass


@contract.command()
@click.option("--unsigned", is_flag=True, help="Show only unsigned contracts")
@click.option("--unpaid", is_flag=True, help="Show only unpaid contracts")
@click.option("--client-id", type=int, help="Filter by client ID")
def list(unsigned: bool, unpaid: bool, client_id: int = None):
    """List contracts"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        contracts = ContractService.list_contracts(
            user, unsigned_only=unsigned, unpaid_only=unpaid, client_id=client_id
        )

        if not contracts:
            console.print("[yellow]No contracts found[/yellow]")
            return

        table = Table(title="Contracts")
        table.add_column("ID", style="cyan")
        table.add_column("Client", style="green")
        table.add_column("Total Amount")
        table.add_column("Amount Due")
        table.add_column("Status", style="yellow")
        table.add_column("Commercial")

        for c in contracts:
            status = "✓ Signed" if c.signed else "⧗ Unsigned"
            client_name = c.client.full_name if c.client else "Unknown"
            commercial_name = c.commercial.full_name if c.commercial else "Unassigned"

            table.add_row(
                str(c.id),
                client_name,
                f"${c.total_amount:,.2f}",
                f"${c.amount_due:,.2f}",
                status,
                commercial_name,
            )

        console.print(table)
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@contract.command()
@click.option("--client-id", prompt=True, type=int, help="Client ID")
@click.option("--total-amount", prompt=True, type=float, help="Total amount")
@click.option("--amount-due", prompt=True, type=float, help="Amount due")
def create(client_id: int, total_amount: float, amount_due: float):
    """Create a new contract"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        contract = ContractService.create_contract(
            client_id=client_id,
            total_amount=Decimal(str(total_amount)),
            amount_due=Decimal(str(amount_due)),
            commercial_id=user.id,
            current_user=user,
        )
        console.print(f"[green]✓[/green] Contract created with ID: {contract.id}")
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@contract.command()
@click.argument("contract_id", type=int)
@click.option("--total-amount", type=float, help="New total amount")
@click.option("--amount-due", type=float, help="New amount due")
@click.option("--signed", type=bool, help="Contract signed status")
def update(
    contract_id: int, total_amount: float = None, amount_due: float = None, signed: bool = None
):
    """Update a contract"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        updated_contract = ContractService.update_contract(
            contract_id=contract_id,
            current_user=user,
            total_amount=Decimal(str(total_amount)) if total_amount else None,
            amount_due=Decimal(str(amount_due)) if amount_due else None,
            signed=signed,
        )
        console.print(f"[green]✓[/green] Contract {updated_contract.id} updated successfully")
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@contract.command()
@click.argument("contract_id", type=int)
def sign(contract_id: int):
    """Sign a contract"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        contract = ContractService.sign_contract(contract_id, user)
        console.print(f"[green]✓[/green] Contract {contract.id} signed successfully")
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")


@contract.command()
@click.argument("contract_id", type=int)
@click.option("--amount", prompt=True, type=float, help="Amount paid")
def payment(contract_id: int, amount: float):
    """Update payment for a contract"""
    user = get_current_user()
    if not user:
        console.print("[red]✗[/red] Please login first")
        return

    try:
        contract = ContractService.update_payment(contract_id, Decimal(str(amount)), user)
        console.print(f"[green]✓[/green] Payment updated. Amount due: ${contract.amount_due:,.2f}")
    except PermissionError as e:
        console.print(f"[red]✗[/red] {e}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
