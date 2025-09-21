"""Base repository interface and implementation."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):
    """Abstract base repository interface."""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        pass
    
    @abstractmethod
    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[T]:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass
    
    @abstractmethod
    async def list(self, filters: Dict[str, Any] = None, limit: int = 50, offset: int = 0) -> List[T]:
        pass

class SQLAlchemyRepository(BaseRepository[T]):
    """SQLAlchemy implementation of base repository."""
    
    def __init__(self, db: Session, model_class):
        self.db = db
        self.model_class = model_class
    
    async def create(self, entity_data: Dict[str, Any]) -> T:
        entity = self.model_class(**entity_data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    async def get_by_id(self, id: str) -> Optional[T]:
        return self.db.query(self.model_class).filter(self.model_class.id == id).first()
    
    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[T]:
        entity = await self.get_by_id(id)
        if not entity:
            return None
        
        for field, value in updates.items():
            setattr(entity, field, value)
        
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    async def delete(self, id: str) -> bool:
        entity = await self.get_by_id(id)
        if not entity:
            return False
        
        self.db.delete(entity)
        self.db.commit()
        return True
    
    async def list(self, filters: Dict[str, Any] = None, limit: int = 50, offset: int = 0) -> List[T]:
        query = self.db.query(self.model_class)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    query = query.filter(getattr(self.model_class, field) == value)
        
        return query.offset(offset).limit(limit).all()