"""Event handlers for system events."""

from typing import List
from ..events.base import EventHandler, Event
from ..core.logging import LoggerMixin

class PaperEventHandler(EventHandler, LoggerMixin):
    """Handler for paper-related events."""
    
    @property
    def event_types(self) -> List[str]:
        return [
            "paper.created",
            "paper.updated", 
            "paper.viewed",
            "paper.processed"
        ]
    
    async def handle(self, event: Event) -> None:
        """Handle paper events."""
        if event.event_type == "paper.created":
            await self._handle_paper_created(event)
        elif event.event_type == "paper.updated":
            await self._handle_paper_updated(event)
        elif event.event_type == "paper.viewed":
            await self._handle_paper_viewed(event)
        elif event.event_type == "paper.processed":
            await self._handle_paper_processed(event)
    
    async def _handle_paper_created(self, event: Event) -> None:
        """Handle paper creation event."""
        paper_id = event.data.get("paper_id")
        self.log_event("paper_created_handled", paper_id=paper_id)
        
        # Trigger background processing
        # This could trigger AI analysis, embedding generation, etc.
    
    async def _handle_paper_updated(self, event: Event) -> None:
        """Handle paper update event."""
        paper_id = event.data.get("paper_id")
        self.log_event("paper_updated_handled", paper_id=paper_id)
    
    async def _handle_paper_viewed(self, event: Event) -> None:
        """Handle paper view event."""
        paper_id = event.data.get("paper_id")
        user_id = event.data.get("user_id")
        # Could update recommendation algorithms, analytics, etc.
    
    async def _handle_paper_processed(self, event: Event) -> None:
        """Handle paper processing completion."""
        paper_id = event.data.get("paper_id")
        self.log_event("paper_processed_handled", paper_id=paper_id)

class AgentEventHandler(EventHandler, LoggerMixin):
    """Handler for agent-related events."""
    
    @property
    def event_types(self) -> List[str]:
        return [
            "agent.created",
            "agent.query_received",
            "agent.response_generated",
            "agent.collaboration_started",
            "agent.collaboration_completed"
        ]
    
    async def handle(self, event: Event) -> None:
        """Handle agent events."""
        if event.event_type == "agent.created":
            await self._handle_agent_created(event)
        elif event.event_type == "agent.query_received":
            await self._handle_query_received(event)
        elif event.event_type == "agent.response_generated":
            await self._handle_response_generated(event)
        elif event.event_type == "agent.collaboration_started":
            await self._handle_collaboration_started(event)
        elif event.event_type == "agent.collaboration_completed":
            await self._handle_collaboration_completed(event)
    
    async def _handle_agent_created(self, event: Event) -> None:
        """Handle agent creation event."""
        agent_id = event.data.get("agent_id")
        self.log_event("agent_created_handled", agent_id=agent_id)
        
        # Initialize agent context, setup monitoring, etc.
    
    async def _handle_query_received(self, event: Event) -> None:
        """Handle agent query event."""
        agent_id = event.data.get("agent_id")
        query = event.data.get("query")
        # Could trigger analytics, logging, etc.
    
    async def _handle_response_generated(self, event: Event) -> None:
        """Handle agent response event."""
        agent_id = event.data.get("agent_id")
        response_time = event.data.get("response_time")
        # Update performance metrics, quality scores, etc.
    
    async def _handle_collaboration_started(self, event: Event) -> None:
        """Handle multi-agent collaboration start."""
        collaboration_id = event.data.get("collaboration_id")
        agent_ids = event.data.get("agent_ids", [])
        self.log_event("collaboration_started", 
                      collaboration_id=collaboration_id, 
                      agent_count=len(agent_ids))
    
    async def _handle_collaboration_completed(self, event: Event) -> None:
        """Handle multi-agent collaboration completion."""
        collaboration_id = event.data.get("collaboration_id")
        processing_time = event.data.get("processing_time")
        self.log_event("collaboration_completed", 
                      collaboration_id=collaboration_id,
                      processing_time=processing_time)

class SystemEventHandler(EventHandler, LoggerMixin):
    """Handler for system-wide events."""
    
    @property
    def event_types(self) -> List[str]:
        return [
            "system.startup",
            "system.shutdown",
            "system.error",
            "system.health_check"
        ]
    
    async def handle(self, event: Event) -> None:
        """Handle system events."""
        if event.event_type == "system.startup":
            await self._handle_startup(event)
        elif event.event_type == "system.shutdown":
            await self._handle_shutdown(event)
        elif event.event_type == "system.error":
            await self._handle_error(event)
        elif event.event_type == "system.health_check":
            await self._handle_health_check(event)
    
    async def _handle_startup(self, event: Event) -> None:
        """Handle system startup."""
        self.log_event("system_startup", timestamp=event.timestamp)
    
    async def _handle_shutdown(self, event: Event) -> None:
        """Handle system shutdown."""
        self.log_event("system_shutdown", timestamp=event.timestamp)
    
    async def _handle_error(self, event: Event) -> None:
        """Handle system errors."""
        error_type = event.data.get("error_type")
        error_message = event.data.get("error_message")
        self.log_error(Exception(error_message), operation="system_error", error_type=error_type)
    
    async def _handle_health_check(self, event: Event) -> None:
        """Handle health check events."""
        status = event.data.get("status")
        self.log_event("health_check", status=status)