"""Model Context Protocol (MCP) implementation for agent-to-agent communication."""

import asyncio
import json
import websockets
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

logger = structlog.get_logger()


class MessageType(Enum):
    """MCP message types."""
    INITIALIZE = "initialize"
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class MCPMessage:
    """MCP protocol message."""
    type: MessageType
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPServer:
    """MCP server for agent-to-agent communication."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.connected_agents: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.server = None
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default MCP message handlers."""
        self.message_handlers.update({
            "agent.register": self._handle_agent_register,
            "agent.query": self._handle_agent_query,
            "agent.broadcast": self._handle_agent_broadcast,
            "conversation.start": self._handle_conversation_start,
            "conversation.message": self._handle_conversation_message,
            "paper.compare": self._handle_paper_compare,
            "paper.synthesize": self._handle_paper_synthesize
        })
    
    async def start_server(self):
        """Start the MCP server."""
        try:
            self.server = await websockets.serve(
                self._handle_connection,
                self.host,
                self.port
            )
            logger.info(f"MCP server started on {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
    
    async def stop_server(self):
        """Stop the MCP server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("MCP server stopped")
    
    async def _handle_connection(self, websocket, path):
        """Handle new WebSocket connection."""
        agent_id = None
        try:
            logger.info(f"New MCP connection from {websocket.remote_address}")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    mcp_message = MCPMessage(**data)
                    
                    # Handle initialization
                    if mcp_message.type == MessageType.INITIALIZE:
                        agent_id = await self._handle_initialize(websocket, mcp_message)
                    
                    # Handle requests
                    elif mcp_message.type == MessageType.REQUEST:
                        await self._handle_request(websocket, mcp_message, agent_id)
                    
                    # Handle notifications
                    elif mcp_message.type == MessageType.NOTIFICATION:
                        await self._handle_notification(websocket, mcp_message, agent_id)
                        
                except json.JSONDecodeError as e:
                    await self._send_error(websocket, None, f"Invalid JSON: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await self._send_error(websocket, None, str(e))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"MCP connection closed for agent: {agent_id}")
        except Exception as e:
            logger.error(f"MCP connection error: {e}")
        finally:
            if agent_id and agent_id in self.connected_agents:
                del self.connected_agents[agent_id]
    
    async def _handle_initialize(
        self,
        websocket: websockets.WebSocketServerProtocol,
        message: MCPMessage
    ) -> str:
        """Handle agent initialization."""
        
        if not message.params or "agent_id" not in message.params:
            await self._send_error(websocket, message.id, "Missing agent_id in initialization")
            return None
        
        agent_id = message.params["agent_id"]
        self.connected_agents[agent_id] = websocket
        
        # Send initialization response
        response = MCPMessage(
            type=MessageType.RESPONSE,
            id=message.id,
            result={
                "status": "initialized",
                "agent_id": agent_id,
                "server_capabilities": [
                    "agent.query",
                    "agent.broadcast",
                    "conversation.start",
                    "conversation.message",
                    "paper.compare",
                    "paper.synthesize"
                ]
            }
        )
        
        await self._send_message(websocket, response)
        logger.info(f"Agent {agent_id} initialized via MCP")
        
        return agent_id
    
    async def _handle_request(
        self,
        websocket: websockets.WebSocketServerProtocol,
        message: MCPMessage,
        agent_id: str
    ):
        """Handle MCP request."""
        
        if message.method in self.message_handlers:
            try:
                handler = self.message_handlers[message.method]
                result = await handler(message.params, agent_id)
                
                response = MCPMessage(
                    type=MessageType.RESPONSE,
                    id=message.id,
                    result=result
                )
                
                await self._send_message(websocket, response)
                
            except Exception as e:
                logger.error(f"Handler error for {message.method}: {e}")
                await self._send_error(websocket, message.id, str(e))
        else:
            await self._send_error(websocket, message.id, f"Unknown method: {message.method}")
    
    async def _handle_notification(
        self,
        websocket: websockets.WebSocketServerProtocol,
        message: MCPMessage,
        agent_id: str
    ):
        """Handle MCP notification."""
        
        if message.method in self.message_handlers:
            try:
                handler = self.message_handlers[message.method]
                await handler(message.params, agent_id)
            except Exception as e:
                logger.error(f"Notification handler error for {message.method}: {e}")
    
    async def _send_message(
        self,
        websocket: websockets.WebSocketServerProtocol,
        message: MCPMessage
    ):
        """Send MCP message."""
        try:
            data = json.dumps(asdict(message), default=str)
            await websocket.send(data)
        except Exception as e:
            logger.error(f"Failed to send MCP message: {e}")
    
    async def _send_error(
        self,
        websocket: websockets.WebSocketServerProtocol,
        message_id: Optional[str],
        error_message: str
    ):
        """Send MCP error message."""
        error_msg = MCPMessage(
            type=MessageType.ERROR,
            id=message_id,
            error={
                "code": -1,
                "message": error_message
            }
        )
        await self._send_message(websocket, error_msg)
    
    async def broadcast_to_agents(
        self,
        message: Dict[str, Any],
        exclude_agent: Optional[str] = None
    ):
        """Broadcast message to all connected agents."""
        
        notification = MCPMessage(
            type=MessageType.NOTIFICATION,
            method="broadcast",
            params=message
        )
        
        for agent_id, websocket in self.connected_agents.items():
            if exclude_agent and agent_id == exclude_agent:
                continue
            
            try:
                await self._send_message(websocket, notification)
            except Exception as e:
                logger.error(f"Failed to broadcast to agent {agent_id}: {e}")
    
    # Message Handlers
    
    async def _handle_agent_register(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Handle agent registration."""
        return {
            "status": "registered",
            "agent_id": agent_id,
            "connected_agents": list(self.connected_agents.keys())
        }
    
    async def _handle_agent_query(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Handle agent query request."""
        target_agent = params.get("target_agent")
        query = params.get("query")
        
        if not target_agent or not query:
            raise ValueError("Missing target_agent or query")
        
        if target_agent not in self.connected_agents:
            raise ValueError(f"Agent {target_agent} not connected")
        
        # Forward query to target agent
        query_message = MCPMessage(
            type=MessageType.REQUEST,
            id=f"query_{agent_id}_{target_agent}",
            method="agent.answer",
            params={
                "query": query,
                "from_agent": agent_id
            }
        )
        
        target_websocket = self.connected_agents[target_agent]
        await self._send_message(target_websocket, query_message)
        
        return {
            "status": "query_sent",
            "target_agent": target_agent,
            "query": query
        }
    
    async def _handle_agent_broadcast(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Handle agent broadcast request."""
        message = params.get("message")
        
        if not message:
            raise ValueError("Missing message")
        
        await self.broadcast_to_agents({
            "from_agent": agent_id,
            "message": message,
            "type": "broadcast"
        }, exclude_agent=agent_id)
        
        return {
            "status": "broadcast_sent",
            "recipients": len(self.connected_agents) - 1
        }
    
    async def _handle_conversation_start(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Handle conversation start request."""
        participants = params.get("participants", [])
        topic = params.get("topic")
        conversation_type = params.get("type", "collaboration")
        
        if not participants or not topic:
            raise ValueError("Missing participants or topic")
        
        # Notify all participants
        for participant in participants:
            if participant in self.connected_agents:
                notification = MCPMessage(
                    type=MessageType.NOTIFICATION,
                    method="conversation.invite",
                    params={
                        "conversation_id": f"conv_{agent_id}_{len(participants)}",
                        "topic": topic,
                        "type": conversation_type,
                        "participants": participants,
                        "initiator": agent_id
                    }
                )
                
                websocket = self.connected_agents[participant]
                await self._send_message(websocket, notification)
        
        return {
            "status": "conversation_started",
            "conversation_id": f"conv_{agent_id}_{len(participants)}",
            "participants": participants
        }
    
    async def _handle_conversation_message(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Handle conversation message."""
        conversation_id = params.get("conversation_id")
        message = params.get("message")
        recipients = params.get("recipients", [])
        
        if not conversation_id or not message:
            raise ValueError("Missing conversation_id or message")
        
        # Forward message to recipients
        for recipient in recipients:
            if recipient in self.connected_agents and recipient != agent_id:
                notification = MCPMessage(
                    type=MessageType.NOTIFICATION,
                    method="conversation.message",
                    params={
                        "conversation_id": conversation_id,
                        "from_agent": agent_id,
                        "message": message
                    }
                )
                
                websocket = self.connected_agents[recipient]
                await self._send_message(websocket, notification)
        
        return {
            "status": "message_sent",
            "recipients": len([r for r in recipients if r in self.connected_agents])
        }
    
    async def _handle_paper_compare(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Handle paper comparison request."""
        papers = params.get("papers", [])
        aspect = params.get("aspect", "methodology")
        
        if len(papers) < 2:
            raise ValueError("Need at least 2 papers to compare")
        
        # Notify relevant agents
        for paper_id in papers:
            if paper_id in self.connected_agents:
                notification = MCPMessage(
                    type=MessageType.NOTIFICATION,
                    method="paper.compare_request",
                    params={
                        "papers": papers,
                        "aspect": aspect,
                        "requester": agent_id
                    }
                )
                
                websocket = self.connected_agents[paper_id]
                await self._send_message(websocket, notification)
        
        return {
            "status": "comparison_initiated",
            "papers": papers,
            "aspect": aspect
        }
    
    async def _handle_paper_synthesize(self, params: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Handle paper synthesis request."""
        papers = params.get("papers", [])
        topic = params.get("topic")
        
        if not papers or not topic:
            raise ValueError("Missing papers or topic")
        
        # Notify relevant agents
        for paper_id in papers:
            if paper_id in self.connected_agents:
                notification = MCPMessage(
                    type=MessageType.NOTIFICATION,
                    method="paper.synthesize_request",
                    params={
                        "papers": papers,
                        "topic": topic,
                        "requester": agent_id
                    }
                )
                
                websocket = self.connected_agents[paper_id]
                await self._send_message(websocket, notification)
        
        return {
            "status": "synthesis_initiated",
            "papers": papers,
            "topic": topic
        }


class MCPClient:
    """MCP client for agents to connect to the server."""
    
    def __init__(self, agent_id: str, server_url: str = "ws://localhost:8765"):
        self.agent_id = agent_id
        self.server_url = server_url
        self.websocket = None
        self.message_handlers: Dict[str, Callable] = {}
        self.connected = False
    
    async def connect(self):
        """Connect to MCP server."""
        try:
            self.websocket = await websockets.connect(self.server_url)
            
            # Send initialization
            init_message = MCPMessage(
                type=MessageType.INITIALIZE,
                id="init",
                params={"agent_id": self.agent_id}
            )
            
            await self._send_message(init_message)
            
            # Wait for initialization response
            response = await self._receive_message()
            if response.type == MessageType.RESPONSE and response.result:
                self.connected = True
                logger.info(f"Agent {self.agent_id} connected to MCP server")
                
                # Start message handling loop
                asyncio.create_task(self._message_loop())
            else:
                raise Exception("Failed to initialize MCP connection")
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MCP server."""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info(f"Agent {self.agent_id} disconnected from MCP server")
    
    async def _send_message(self, message: MCPMessage):
        """Send message to server."""
        if self.websocket:
            data = json.dumps(asdict(message), default=str)
            await self.websocket.send(data)
    
    async def _receive_message(self) -> MCPMessage:
        """Receive message from server."""
        if self.websocket:
            data = await self.websocket.recv()
            message_data = json.loads(data)
            return MCPMessage(**message_data)
    
    async def _message_loop(self):
        """Handle incoming messages."""
        try:
            while self.connected and self.websocket:
                message = await self._receive_message()
                
                if message.type == MessageType.REQUEST:
                    await self._handle_request(message)
                elif message.type == MessageType.NOTIFICATION:
                    await self._handle_notification(message)
                    
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            logger.info(f"MCP connection closed for agent {self.agent_id}")
        except Exception as e:
            logger.error(f"MCP message loop error: {e}")
            self.connected = False
    
    async def _handle_request(self, message: MCPMessage):
        """Handle incoming request."""
        if message.method in self.message_handlers:
            try:
                handler = self.message_handlers[message.method]
                result = await handler(message.params)
                
                response = MCPMessage(
                    type=MessageType.RESPONSE,
                    id=message.id,
                    result=result
                )
                
                await self._send_message(response)
                
            except Exception as e:
                error_response = MCPMessage(
                    type=MessageType.ERROR,
                    id=message.id,
                    error={"code": -1, "message": str(e)}
                )
                await self._send_message(error_response)
    
    async def _handle_notification(self, message: MCPMessage):
        """Handle incoming notification."""
        if message.method in self.message_handlers:
            try:
                handler = self.message_handlers[message.method]
                await handler(message.params)
            except Exception as e:
                logger.error(f"Notification handler error: {e}")
    
    def register_handler(self, method: str, handler: Callable):
        """Register message handler."""
        self.message_handlers[method] = handler
    
    async def send_request(self, method: str, params: Dict[str, Any]) -> Any:
        """Send request to server."""
        if not self.connected:
            raise Exception("Not connected to MCP server")
        
        request = MCPMessage(
            type=MessageType.REQUEST,
            id=f"req_{method}_{asyncio.get_event_loop().time()}",
            method=method,
            params=params
        )
        
        await self._send_message(request)
        
        # Wait for response (simplified - in production, use proper request/response matching)
        response = await self._receive_message()
        if response.type == MessageType.RESPONSE:
            return response.result
        elif response.type == MessageType.ERROR:
            raise Exception(response.error["message"])
    
    async def send_notification(self, method: str, params: Dict[str, Any]):
        """Send notification to server."""
        if not self.connected:
            raise Exception("Not connected to MCP server")
        
        notification = MCPMessage(
            type=MessageType.NOTIFICATION,
            method=method,
            params=params
        )
        
        await self._send_message(notification)