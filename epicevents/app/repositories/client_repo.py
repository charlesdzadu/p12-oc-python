from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from .base import BaseRepository
from ..models.client import Client
from ..auth.models import User


class ClientRepository(BaseRepository[Client]):
    def __init__(self, session: Session):
        super().__init__(session, Client)

    def get_by_id(self, id: int) -> Optional[Client]:
        statement = select(Client).where(Client.id == id).options(selectinload(Client.commercial))
        return self.session.exec(statement).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Client]:
        statement = select(Client).offset(skip).limit(limit).options(selectinload(Client.commercial))
        return self.session.exec(statement).all()

    def get_by_email(self, email: str) -> Optional[Client]:
        statement = select(Client).where(Client.email == email).options(selectinload(Client.commercial))
        return self.session.exec(statement).first()

    def get_by_commercial(self, commercial_id: int) -> List[Client]:
        statement = select(Client).where(Client.commercial_id == commercial_id).options(selectinload(Client.commercial))
        return self.session.exec(statement).all()

    def search_by_name(self, name: str) -> List[Client]:
        statement = select(Client).where(
            Client.full_name.contains(name) | Client.company_name.contains(name)
        ).options(selectinload(Client.commercial))
        return self.session.exec(statement).all()

    def get_clients_without_commercial(self) -> List[Client]:
        statement = select(Client).where(Client.commercial_id == None).options(selectinload(Client.commercial))
        return self.session.exec(statement).all()

    def assign_commercial(self, client_id: int, commercial_id: int) -> Optional[Client]:
        client = self.get_by_id(client_id)
        if client:
            client.commercial_id = commercial_id
            self.session.add(client)
            self.session.commit()
            self.session.refresh(client)
        return client
