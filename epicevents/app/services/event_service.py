from typing import List, Optional
from datetime import datetime
from ..database import get_session
from ..repositories.event_repo import EventRepository
from ..repositories.contract_repo import ContractRepository
from ..models.event import Event
from ..auth.models import User


class EventService:
    @staticmethod
    def create_event(
        name: str,
        contract_id: int,
        event_date_start: datetime,
        event_date_end: datetime,
        location: str,
        attendees: int,
        notes: Optional[str],
        current_user: User,
    ) -> Event:
        if not current_user.has_permission("create", "event"):
            raise PermissionError("You don't have permission to create events")

        with get_session() as session:
            repo = EventRepository(session)
            contract_repo = ContractRepository(session)

            contract = contract_repo.get_by_id(contract_id)
            if not contract:
                raise ValueError(f"Contract with ID {contract_id} not found")

            if not contract.signed:
                raise ValueError("Cannot create event for unsigned contract")

            if current_user.is_commercial:
                if contract.commercial_id != current_user.id:
                    raise PermissionError("You can only create events for your contracts")

            event = repo.create(
                name=name,
                contract_id=contract_id,
                event_date_start=event_date_start,
                event_date_end=event_date_end,
                location=location,
                attendees=attendees,
                notes=notes,
            )
            return event

    @staticmethod
    def update_event(
        event_id: int,
        current_user: User,
        name: Optional[str] = None,
        event_date_start: Optional[datetime] = None,
        event_date_end: Optional[datetime] = None,
        location: Optional[str] = None,
        attendees: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Event:
        with get_session() as session:
            repo = EventRepository(session)
            event = repo.get_by_id(event_id)

            if not event:
                raise ValueError(f"Event with ID {event_id} not found")

            if current_user.is_support:
                if event.support_contact_id != current_user.id:
                    raise PermissionError("You can only update events assigned to you")
            elif not current_user.is_management:
                raise PermissionError("You don't have permission to update events")

            update_data = {}
            if name is not None:
                update_data["name"] = name
            if event_date_start is not None:
                update_data["event_date_start"] = event_date_start
            if event_date_end is not None:
                update_data["event_date_end"] = event_date_end
            if location is not None:
                update_data["location"] = location
            if attendees is not None:
                update_data["attendees"] = attendees
            if notes is not None:
                update_data["notes"] = notes

            updated_event = repo.update(event_id, **update_data)
            return updated_event

    @staticmethod
    def assign_support_contact(event_id: int, support_contact_id: int, current_user: User) -> Event:
        if not current_user.is_management:
            raise PermissionError("Only management can assign support contacts")

        with get_session() as session:
            from ..auth.service import AuthService

            support_user = AuthService.get_current_user(support_contact_id)
            if not support_user or not support_user.is_support:
                raise ValueError("Invalid support contact ID")

            repo = EventRepository(session)
            event = repo.get_by_id(event_id)

            if not event:
                raise ValueError(f"Event with ID {event_id} not found")

            return repo.assign_support_contact(event_id, support_contact_id)

    @staticmethod
    def get_event(event_id: int, current_user: User) -> Optional[Event]:
        if not current_user.has_permission("read", "event"):
            raise PermissionError("You don't have permission to view events")

        with get_session() as session:
            repo = EventRepository(session)
            return repo.get_by_id(event_id)

    @staticmethod
    def list_events(
        current_user: User,
        without_support: bool = False,
        upcoming_only: bool = False,
        past_only: bool = False,
        contract_id: Optional[int] = None,
    ) -> List[Event]:
        if not current_user.has_permission("read", "event"):
            raise PermissionError("You don't have permission to view events")

        with get_session() as session:
            repo = EventRepository(session)

            if without_support:
                return repo.get_events_without_support()
            elif upcoming_only:
                return repo.get_upcoming_events()
            elif past_only:
                return repo.get_past_events()
            elif contract_id:
                return repo.get_by_contract(contract_id)
            elif current_user.is_support:
                return repo.get_by_support_contact(current_user.id)
            else:
                return repo.get_all()

    @staticmethod
    def search_events_by_location(location: str, current_user: User) -> List[Event]:
        if not current_user.has_permission("read", "event"):
            raise PermissionError("You don't have permission to search events")

        with get_session() as session:
            repo = EventRepository(session)
            return repo.search_by_location(location)
