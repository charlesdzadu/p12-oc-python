from typing import TypeVar, Generic, List, Optional, Type, Dict, Any
from sqlmodel import SQLModel, Session, select, func
from abc import ABC, abstractmethod


ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType], ABC):
    def __init__(self, session: Session, model: Type[ModelType]):
        self.session = session
        self.model = model

    def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def get_by_id(self, id: int) -> Optional[ModelType]:
        return self.session.get(self.model, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        statement = select(self.model).offset(skip).limit(limit)
        results = self.session.exec(statement)
        return results.all()

    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        instance = self.get_by_id(id)
        if not instance:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key) and value is not None:
                setattr(instance, key, value)

        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def delete(self, id: int) -> bool:
        instance = self.get_by_id(id)
        if not instance:
            return False

        self.session.delete(instance)
        self.session.commit()
        return True

    def count(self) -> int:
        statement = select(func.count()).select_from(self.model)
        return self.session.exec(statement).one()

    def filter_by(self, **kwargs) -> List[ModelType]:
        statement = select(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                statement = statement.where(getattr(self.model, key) == value)

        results = self.session.exec(statement)
        return results.all()
