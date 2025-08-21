from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from .client import Client
    from .event import Event
    from ..auth.models import User


class Contract(SQLModel, table=True):
    __tablename__ = "contracts"

    id: Optional[int] = Field(default=None, primary_key=True)
    total_amount: Decimal = Field(nullable=False, decimal_places=2, max_digits=10)
    amount_due: Decimal = Field(nullable=False, decimal_places=2, max_digits=10)
    created_at: datetime = Field(default_factory=datetime.now)
    signed: bool = Field(default=False)

    client_id: int = Field(foreign_key="clients.id", nullable=False)
    client: "Client" = Relationship(back_populates="contracts")

    commercial_id: Optional[int] = Field(foreign_key="users.id")
    commercial: Optional["User"] = Relationship(back_populates="contracts")

    events: List["Event"] = Relationship(back_populates="contract")

    def __repr__(self):
        return f"<Contract {self.id} - Client: {self.client_id} - Signed: {self.signed}>"

    @property
    def amount_paid(self) -> Decimal:
        return self.total_amount - self.amount_due

    def sign_contract(self):
        self.signed = True

    def update_payment(self, amount_paid: Decimal):
        self.amount_due = max(Decimal(0), self.total_amount - amount_paid)
