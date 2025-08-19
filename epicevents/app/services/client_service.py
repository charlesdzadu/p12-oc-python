from typing import List, Optional
from ..database import get_session
from ..repositories.client_repo import ClientRepository
from ..models.client import Client
from ..auth.models import User, Department


class ClientService:
    @staticmethod
    def create_client(
        full_name: str,
        email: str,
        phone: str,
        company_name: str,
        commercial_id: int,
        current_user: User,
    ) -> Client:
        if not current_user.has_permission("create", "client"):
            raise PermissionError("You don't have permission to create clients")

        with get_session() as session:
            repo = ClientRepository(session)

            existing_client = repo.get_by_email(email)
            if existing_client:
                raise ValueError(f"Client with email {email} already exists")

            client = repo.create(
                full_name=full_name,
                email=email,
                phone=phone,
                company_name=company_name,
                commercial_id=commercial_id,
            )
            return client

    @staticmethod
    def update_client(
        client_id: int,
        current_user: User,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company_name: Optional[str] = None,
        commercial_id: Optional[int] = None,
    ) -> Client:
        with get_session() as session:
            repo = ClientRepository(session)
            client = repo.get_by_id(client_id)

            if not client:
                raise ValueError(f"Client with ID {client_id} not found")

            if current_user.is_commercial:
                if client.commercial_id != current_user.id:
                    raise PermissionError("You can only update your own clients")
            elif not current_user.is_management:
                raise PermissionError("You don't have permission to update clients")

            if email and email != client.email:
                existing = repo.get_by_email(email)
                if existing:
                    raise ValueError(f"Email {email} is already in use")

            update_data = {}
            if full_name is not None:
                update_data["full_name"] = full_name
            if email is not None:
                update_data["email"] = email
            if phone is not None:
                update_data["phone"] = phone
            if company_name is not None:
                update_data["company_name"] = company_name
            if commercial_id is not None and current_user.is_management:
                update_data["commercial_id"] = commercial_id

            updated_client = repo.update(client_id, **update_data)
            return updated_client

    @staticmethod
    def get_client(client_id: int, current_user: User) -> Optional[Client]:
        if not current_user.has_permission("read", "client"):
            raise PermissionError("You don't have permission to view clients")

        with get_session() as session:
            repo = ClientRepository(session)
            return repo.get_by_id(client_id)

    @staticmethod
    def list_clients(
        current_user: User, filter_commercial_id: Optional[int] = None
    ) -> List[Client]:
        if not current_user.has_permission("read", "client"):
            raise PermissionError("You don't have permission to view clients")

        with get_session() as session:
            repo = ClientRepository(session)

            if filter_commercial_id:
                return repo.get_by_commercial(filter_commercial_id)
            elif current_user.is_commercial:
                return repo.get_by_commercial(current_user.id)
            else:
                return repo.get_all()

    @staticmethod
    def search_clients(query: str, current_user: User) -> List[Client]:
        if not current_user.has_permission("read", "client"):
            raise PermissionError("You don't have permission to search clients")

        with get_session() as session:
            repo = ClientRepository(session)
            return repo.search_by_name(query)
