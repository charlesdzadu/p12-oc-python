from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .contract import Contract
    from ..auth.models import User


class Client(SQLModel, table=True):
    __tablename__ = "clients"

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str = Field(nullable=False, index=True)
    email: str = Field(nullable=False, unique=True, index=True)
    phone: str = Field(nullable=False)
    company_name: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    commercial_id: Optional[int] = Field(default=None, foreign_key="users.id")
    commercial: Optional["User"] = Relationship(back_populates="clients")

    contracts: List["Contract"] = Relationship(back_populates="client")

    def __repr__(self):
        return f"<Client {self.full_name} - {self.company_name}>"

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        self.updated_at = datetime.now()
