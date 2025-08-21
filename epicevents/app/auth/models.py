from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING, ForwardRef
from enum import Enum

if TYPE_CHECKING:
    from ..models.client import Client
    from ..models.contract import Contract
    from ..models.event import Event


class Department(str, Enum):
    COMMERCIAL = "COMMERCIAL"
    SUPPORT = "SUPPORT"
    MANAGEMENT = "MANAGEMENT"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: str = Field(nullable=False, unique=True, index=True)
    full_name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True, index=True)
    password_hash: str = Field(nullable=False)
    department: Department = Field(nullable=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    clients: List["Client"] = Relationship(back_populates="commercial")  # type: ignore
    contracts: List["Contract"] = Relationship(back_populates="commercial")  # type: ignore
    events: List["Event"] = Relationship(back_populates="support_contact")  # type: ignore

    def __repr__(self):
        return f"<User {self.full_name} - {self.department}>"

    @property
    def is_management(self) -> bool:
        return self.department == Department.MANAGEMENT

    @property
    def is_commercial(self) -> bool:
        return self.department == Department.COMMERCIAL

    @property
    def is_support(self) -> bool:
        return self.department == Department.SUPPORT

    def has_permission(self, action: str, resource: str) -> bool:
        permissions = {
            Department.MANAGEMENT: {
                "create": ["user", "contract", "event"],
                "update": ["user", "contract", "event"],
                "delete": ["user"],
                "read": ["user", "client", "contract", "event"],
            },
            Department.COMMERCIAL: {
                "create": ["client", "event"],
                "update": ["client", "contract"],
                "delete": [],
                "read": ["client", "contract", "event"],
            },
            Department.SUPPORT: {
                "create": [],
                "update": ["event"],
                "delete": [],
                "read": ["client", "contract", "event"],
            },
        }

        dept_permissions = permissions.get(self.department, {})
        allowed_resources = dept_permissions.get(action, [])
        return resource in allowed_resources
