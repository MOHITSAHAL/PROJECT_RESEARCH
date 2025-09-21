"""Base event system for decoupled communication."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from dataclasses import dataclass
import asyncio
import json
from uuid import uuid4

@dataclass
class Event:
    """Base event class."""
    id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "correlation_id": self.correlation_id
        }

class EventHandler(ABC):
    """Abstract event handler."""
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        pass
    
    @property
    @abstractmethod
    def event_types(self) -> List[str]:
        pass

class EventBus:
    """Simple in-memory event bus."""
    
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._middleware: List[Callable[[Event], Event]] = []
    
    def subscribe(self, handler: EventHandler) -> None:
        """Subscribe handler to event types."""
        for event_type in handler.event_types:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
    
    def add_middleware(self, middleware: Callable[[Event], Event]) -> None:
        """Add middleware to process events."""
        self._middleware.append(middleware)
    
    async def publish(self, event: Event) -> None:
        """Publish event to all subscribers."""
        # Apply middleware
        for middleware in self._middleware:
            event = middleware(event)
        
        # Get handlers for event type
        handlers = self._handlers.get(event.event_type, [])
        
        # Execute handlers concurrently
        if handlers:
            tasks = [handler.handle(event) for handler in handlers]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def create_event(self, event_type: str, data: Dict[str, Any], 
                    source: str, correlation_id: Optional[str] = None) -> Event:
        """Create a new event."""
        return Event(
            id=str(uuid4()),
            event_type=event_type,
            data=data,
            timestamp=datetime.utcnow(),
            source=source,
            correlation_id=correlation_id
        )

# Global event bus instance
event_bus = EventBus()