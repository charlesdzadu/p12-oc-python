from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .contract import Contract
    from .client import Client
    from ..auth.models import User


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    event_date_start: datetime = Field(nullable=False)
    event_date_end: datetime = Field(nullable=False)
    location: str = Field(nullable=False)
    attendees: int = Field(nullable=False)
    notes: Optional[str] = Field(default=None)

    contract_id: int = Field(foreign_key="contracts.id", nullable=False)
    contract: "Contract" = Relationship(back_populates="events")

    support_contact_id: Optional[int] = Field(foreign_key="users.id")
    support_contact: Optional["User"] = Relationship(back_populates="events")

    @property
    def client(self) -> Optional["Client"]:
        if self.contract:
            return self.contract.client
        return None

    @property
    def client_contact(self) -> Optional[str]:
        if self.client:
            return f"{self.client.full_name} - {self.client.email} - {self.client.phone}"
        return None

    def __repr__(self):
        return f"<Event {self.name} - {self.event_date_start}>"

    def assign_support(self, support_user_id: int):
        self.support_contact_id = support_user_id
