from typing import List, Optional
from sqlmodel import Session, select
from datetime import datetime
from .base import BaseRepository
from ..models.event import Event


class EventRepository(BaseRepository[Event]):
    def __init__(self, session: Session):
        super().__init__(session, Event)

    def get_by_contract(self, contract_id: int) -> List[Event]:
        statement = select(Event).where(Event.contract_id == contract_id)
        return self.session.exec(statement).all()

    def get_by_support_contact(self, support_contact_id: int) -> List[Event]:
        statement = select(Event).where(Event.support_contact_id == support_contact_id)
        return self.session.exec(statement).all()

    def get_events_without_support(self) -> List[Event]:
        statement = select(Event).where(Event.support_contact_id == None)
        return self.session.exec(statement).all()

    def get_upcoming_events(self) -> List[Event]:
        now = datetime.utcnow()
        statement = (
            select(Event).where(Event.event_date_start > now).order_by(Event.event_date_start)
        )
        return self.session.exec(statement).all()

    def get_past_events(self) -> List[Event]:
        now = datetime.utcnow()
        statement = (
            select(Event).where(Event.event_date_end < now).order_by(Event.event_date_end.desc())
        )
        return self.session.exec(statement).all()

    def get_events_in_date_range(self, start_date: datetime, end_date: datetime) -> List[Event]:
        statement = select(Event).where(
            (Event.event_date_start >= start_date) & (Event.event_date_end <= end_date)
        )
        return self.session.exec(statement).all()

    def assign_support_contact(self, event_id: int, support_contact_id: int) -> Optional[Event]:
        event = self.get_by_id(event_id)
        if event:
            event.assign_support(support_contact_id)
            self.session.add(event)
            self.session.commit()
            self.session.refresh(event)
        return event

    def search_by_location(self, location: str) -> List[Event]:
        statement = select(Event).where(Event.location.contains(location))
        return self.session.exec(statement).all()
