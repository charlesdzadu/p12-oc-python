from typing import List, Optional
from sqlmodel import Session, select
from decimal import Decimal
from .base import BaseRepository
from ..models.contract import Contract


class ContractRepository(BaseRepository[Contract]):
    def __init__(self, session: Session):
        super().__init__(session, Contract)

    def get_by_client(self, client_id: int) -> List[Contract]:
        statement = select(Contract).where(Contract.client_id == client_id)
        return self.session.exec(statement).all()

    def get_by_commercial(self, commercial_id: int) -> List[Contract]:
        statement = select(Contract).where(Contract.commercial_id == commercial_id)
        return self.session.exec(statement).all()

    def get_unsigned_contracts(self) -> List[Contract]:
        statement = select(Contract).where(Contract.signed == False)
        return self.session.exec(statement).all()

    def get_unpaid_contracts(self) -> List[Contract]:
        statement = select(Contract).where(Contract.amount_due > 0)
        return self.session.exec(statement).all()

    def sign_contract(self, contract_id: int) -> Optional[Contract]:
        contract = self.get_by_id(contract_id)
        if contract:
            contract.sign_contract()
            self.session.add(contract)
            self.session.commit()
            self.session.refresh(contract)
        return contract

    def update_payment(self, contract_id: int, amount_paid: Decimal) -> Optional[Contract]:
        contract = self.get_by_id(contract_id)
        if contract:
            contract.update_payment(amount_paid)
            self.session.add(contract)
            self.session.commit()
            self.session.refresh(contract)
        return contract

    def get_contracts_with_events(self) -> List[Contract]:
        from ..models.event import Event

        statement = select(Contract).join(Event, isouter=True).distinct()
        return self.session.exec(statement).all()
