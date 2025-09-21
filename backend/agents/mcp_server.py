"""Model Context Protocol (MCP) server for agent-to-agent communication."""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.logging import LoggerMixin


class MessageType(Enum):
    """MCP message types."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class MCPMessage:
    """MCP message structure."""
    id: str
    type: MessageType
    sender: str
    recipient: str
    method: str
    params: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None


@dataclass
class MCPResponse:
    """MCP response structure."""
    id: str
    correlation_id: str
    sender: str
    recipient: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class MCPServer(LoggerMixin):
    """Model Context Protocol server for agent communication."""
    
    def __init__(self):
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        
        # Register default handlers
        self._register_default_handlers()
    
    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> bool:
        """Register an agent with the MCP server."""
        try:
            self.registered_agents[agent_id] = {
                "agent_id": agent_id,
                "capabilities": agent_info.get("capabilities", []),
                "specialization": agent_info.get("specialization"),
                "model_name": agent_info.get("model_name"),
                "status": "active",
                "registered_at": datetime.utcnow(),
                "last_seen": datetime.utcnow()
            }
            
            self.log_event("agent_registered_mcp", agent_id=agent_id)
            return True
            
        except Exception as e:
            self.log_error(e, operation="register_agent", agent_id=agent_id)
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the MCP server."""
        if agent_id in self.registered_agents:
            del self.registered_agents[agent_id]
            
            # Clean up any active sessions
            sessions_to_remove = [
                session_id for session_id, session in self.active_sessions.items()
                if agent_id in session.get("participants", [])
            ]
            
            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]
            
            self.log_event("agent_unregistered_mcp", agent_id=agent_id)
            return True
        
        return False
    
    async def send_message(self, message: MCPMessage) -> Optional[MCPResponse]:
        """Send a message to an agent."""
        try:
            # Validate recipient exists
            if message.recipient not in self.registered_agents:
                return MCPResponse(
                    id=message.id,
                    correlation_id=message.id,
                    sender="mcp_server",
                    recipient=message.sender,
                    error={"code": "AGENT_NOT_FOUND", "message": f"Agent {message.recipient} not found"}
                )
            
            # Update last seen for sender
            if message.sender in self.registered_agents:
                self.registered_agents[message.sender]["last_seen"] = datetime.utcnow()
            
            # Route message to appropriate handler
            handler = self.message_handlers.get(message.method)
            if not handler:
                return MCPResponse(
                    id=message.id,
                    correlation_id=message.id,
                    sender="mcp_server",
                    recipient=message.sender,
                    error={"code": "METHOD_NOT_FOUND", "message": f"Method {message.method} not supported"}
                )
            
            # Process message
            result = await handler(message)
            
            # Create response
            response = MCPResponse(
                id=f"resp_{message.id}",
                correlation_id=message.id,
                sender="mcp_server",
                recipient=message.sender,
                result=result,
                timestamp=datetime.utcnow()
            )
            
            self.log_event("mcp_message_processed", 
                          sender=message.sender, 
                          recipient=message.recipient, 
                          method=message.method)
            
            return response
            
        except Exception as e:
            self.log_error(e, operation="send_message", message_id=message.id)
            return MCPResponse(
                id=message.id,
                correlation_id=message.id,
                sender="mcp_server",
                recipient=message.sender,
                error={"code": "INTERNAL_ERROR", "message": str(e)}
            )
    
    async def broadcast_message(self, message: MCPMessage, target_agents: Optional[List[str]] = None) -> List[MCPResponse]:
        """Broadcast a message to multiple agents."""
        responses = []
        
        # Determine target agents
        if target_agents is None:
            target_agents = list(self.registered_agents.keys())
        
        # Send to each target agent
        for agent_id in target_agents:
            if agent_id == message.sender:  # Don't send to sender
                continue
            
            # Create individual message
            individual_message = MCPMessage(
                id=f"{message.id}_{agent_id}",
                type=message.type,
                sender=message.sender,
                recipient=agent_id,
                method=message.method,
                params=message.params,
                timestamp=message.timestamp,
                correlation_id=message.correlation_id
            )
            
            response = await self.send_message(individual_message)
            if response:
                responses.append(response)
        
        return responses
    
    def create_session(self, session_id: str, participants: List[str], session_config: Dict[str, Any]) -> bool:
        """Create a communication session between agents."""
        try:
            # Validate all participants are registered
            for participant in participants:
                if participant not in self.registered_agents:
                    raise ValueError(f"Agent {participant} not registered")
            
            self.active_sessions[session_id] = {
                "session_id": session_id,
                "participants": participants,
                "config": session_config,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "message_count": 0
            }
            
            self.log_event("mcp_session_created", session_id=session_id, participants=participants)
            return True
            
        except Exception as e:
            self.log_error(e, operation="create_session", session_id=session_id)
            return False
    
    def end_session(self, session_id: str) -> bool:
        """End a communication session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            del self.active_sessions[session_id]
            
            self.log_event("mcp_session_ended", 
                          session_id=session_id, 
                          duration=(datetime.utcnow() - session["created_at"]).total_seconds())
            return True
        
        return False
    
    async def start_server(self):
        """Start the MCP server."""
        self.running = True
        self.log_event("mcp_server_started")
        
        # Start message processing loop
        asyncio.create_task(self._process_message_queue())
    
    async def stop_server(self):
        """Stop the MCP server."""
        self.running = False
        self.log_event("mcp_server_stopped")
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered agent."""
        return self.registered_agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents."""
        return list(self.registered_agents.values())
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an active session."""
        return self.active_sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        return list(self.active_sessions.values())
    
    def _register_default_handlers(self):
        """Register default message handlers."""
        self.message_handlers.update({
            "query": self._handle_query,
            "collaborate": self._handle_collaborate,
            "share_context": self._handle_share_context,
            "request_assistance": self._handle_request_assistance,
            "provide_feedback": self._handle_provide_feedback,
            "sync_state": self._handle_sync_state
        })
    
    async def _handle_query(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle query messages between agents."""
        query = message.params.get("query", "")
        context = message.params.get("context", {})
        
        # Forward query to recipient agent
        # In a real implementation, this would interface with the actual agent
        return {
            "response": f"Processed query from {message.sender}: {query}",
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_collaborate(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle collaboration requests between agents."""
        task = message.params.get("task", "")
        collaboration_mode = message.params.get("mode", "sequential")
        
        # Create collaboration session
        session_id = f"collab_{message.sender}_{message.recipient}_{datetime.utcnow().timestamp()}"
        
        session_created = self.create_session(
            session_id,
            [message.sender, message.recipient],
            {
                "type": "collaboration",
                "task": task,
                "mode": collaboration_mode
            }
        )
        
        return {
            "session_id": session_id if session_created else None,
            "status": "collaboration_initiated" if session_created else "failed",
            "task": task,
            "mode": collaboration_mode
        }
    
    async def _handle_share_context(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle context sharing between agents."""
        context_data = message.params.get("context", {})
        context_type = message.params.get("type", "general")
        
        # Store shared context (in real implementation, this would be persisted)
        return {
            "status": "context_received",
            "context_type": context_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_request_assistance(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle assistance requests between agents."""
        assistance_type = message.params.get("assistance_type", "general")
        details = message.params.get("details", "")
        
        return {
            "status": "assistance_request_received",
            "assistance_type": assistance_type,
            "response": f"Agent {message.recipient} can provide assistance with {assistance_type}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_provide_feedback(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle feedback between agents."""
        feedback_type = message.params.get("feedback_type", "general")
        feedback_content = message.params.get("content", "")
        rating = message.params.get("rating")
        
        return {
            "status": "feedback_received",
            "feedback_type": feedback_type,
            "rating": rating,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_sync_state(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle state synchronization between agents."""
        state_data = message.params.get("state", {})
        sync_type = message.params.get("sync_type", "full")
        
        return {
            "status": "state_synced",
            "sync_type": sync_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _process_message_queue(self):
        """Process messages from the queue."""
        while self.running:
            try:
                # Wait for messages with timeout
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                # Process message
                response = await self.send_message(message)
                
                # Mark task as done
                self.message_queue.task_done()
                
            except asyncio.TimeoutError:
                # No messages to process, continue
                continue
            except Exception as e:
                self.log_error(e, operation="process_message_queue")
    
    def register_custom_handler(self, method: str, handler: Callable):
        """Register a custom message handler."""
        self.message_handlers[method] = handler
        self.log_event("custom_handler_registered", method=method)
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get MCP server statistics."""
        return {
            "registered_agents": len(self.registered_agents),
            "active_sessions": len(self.active_sessions),
            "supported_methods": list(self.message_handlers.keys()),
            "server_running": self.running,
            "queue_size": self.message_queue.qsize()
        }


# Global MCP server instance
mcp_server = MCPServer()