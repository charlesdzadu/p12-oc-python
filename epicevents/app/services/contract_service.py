from typing import List, Optional
from decimal import Decimal
from ..database import get_session
from ..repositories.contract_repo import ContractRepository
from ..repositories.client_repo import ClientRepository
from ..models.contract import Contract
from ..auth.models import User
from ..utils.logging import log_contract_signed


class ContractService:
    @staticmethod
    def create_contract(
        client_id: int,
        total_amount: Decimal,
        amount_due: Decimal,
        commercial_id: int,
        current_user: User,
    ) -> Contract:
        if not current_user.has_permission("create", "contract"):
            raise PermissionError("You don't have permission to create contracts")

        with get_session() as session:
            repo = ContractRepository(session)
            client_repo = ClientRepository(session)

            client = client_repo.get_by_id(client_id)
            if not client:
                raise ValueError(f"Client with ID {client_id} not found")

            contract = repo.create(
                client_id=client_id,
                total_amount=total_amount,
                amount_due=amount_due,
                commercial_id=commercial_id,
                signed=False,
            )
            return contract

    @staticmethod
    def update_contract(
        contract_id: int,
        current_user: User,
        total_amount: Optional[Decimal] = None,
        amount_due: Optional[Decimal] = None,
        signed: Optional[bool] = None,
    ) -> Contract:
        with get_session() as session:
            repo = ContractRepository(session)
            contract = repo.get_by_id(contract_id)

            if not contract:
                raise ValueError(f"Contract with ID {contract_id} not found")

            if current_user.is_commercial:
                if contract.commercial_id != current_user.id:
                    raise PermissionError("You can only update contracts for your clients")
            elif not current_user.is_management:
                raise PermissionError("You don't have permission to update contracts")

            update_data = {}
            if total_amount is not None:
                update_data["total_amount"] = total_amount
            if amount_due is not None:
                update_data["amount_due"] = amount_due
            if signed is not None:
                update_data["signed"] = signed

            updated_contract = repo.update(contract_id, **update_data)
            return updated_contract

    @staticmethod
    def sign_contract(contract_id: int, current_user: User) -> Contract:
        with get_session() as session:
            repo = ContractRepository(session)
            contract = repo.get_by_id(contract_id)

            if not contract:
                raise ValueError(f"Contract with ID {contract_id} not found")

            if current_user.is_commercial:
                if contract.commercial_id != current_user.id:
                    raise PermissionError("You can only sign contracts for your clients")
            elif not current_user.is_management:
                raise PermissionError("You don't have permission to sign contracts")

            if contract.signed:
                raise ValueError("Contract is already signed")

            signed_contract = repo.sign_contract(contract_id)
            log_contract_signed(contract_id, contract.client_id, current_user.email)
            return signed_contract

    @staticmethod
    def update_payment(contract_id: int, amount_paid: Decimal, current_user: User) -> Contract:
        with get_session() as session:
            repo = ContractRepository(session)
            contract = repo.get_by_id(contract_id)

            if not contract:
                raise ValueError(f"Contract with ID {contract_id} not found")

            if current_user.is_commercial:
                if contract.commercial_id != current_user.id:
                    raise PermissionError("You can only update payments for your contracts")
            elif not current_user.is_management:
                raise PermissionError("You don't have permission to update payments")

            return repo.update_payment(contract_id, amount_paid)

    @staticmethod
    def get_contract(contract_id: int, current_user: User) -> Optional[Contract]:
        if not current_user.has_permission("read", "contract"):
            raise PermissionError("You don't have permission to view contracts")

        with get_session() as session:
            repo = ContractRepository(session)
            return repo.get_by_id(contract_id)

    @staticmethod
    def list_contracts(
        current_user: User,
        unsigned_only: bool = False,
        unpaid_only: bool = False,
        client_id: Optional[int] = None,
    ) -> List[Contract]:
        if not current_user.has_permission("read", "contract"):
            raise PermissionError("You don't have permission to view contracts")

        with get_session() as session:
            repo = ContractRepository(session)

            if unsigned_only:
                return repo.get_unsigned_contracts()
            elif unpaid_only:
                return repo.get_unpaid_contracts()
            elif client_id:
                return repo.get_by_client(client_id)
            elif current_user.is_commercial:
                return repo.get_by_commercial(current_user.id)
            else:
                return repo.get_all()
