"""WebSocket service for real-time communication."""

import json
from typing import Dict, List, Optional
from fastapi import WebSocket
from ..core.logging import LoggerMixin


class WebSocketManager(LoggerMixin):
    """Manages WebSocket connections for real-time communication."""
    
    def __init__(self):
        # Store active connections: connection_id -> websocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Store connection metadata: connection_id -> metadata
        self.connection_metadata: Dict[str, Dict] = {}
        # Store room memberships: room_id -> set of connection_ids
        self.rooms: Dict[str, set] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, metadata: Optional[Dict] = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = metadata or {}
        
        self.log_event("websocket_connected", connection_id=connection_id, metadata=metadata)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        # Find connection_id by websocket
        connection_id = None
        for conn_id, ws in self.active_connections.items():
            if ws == websocket:
                connection_id = conn_id
                break
        
        if connection_id:
            # Remove from all rooms
            for room_id, members in self.rooms.items():
                members.discard(connection_id)
            
            # Clean up empty rooms
            self.rooms = {room_id: members for room_id, members in self.rooms.items() if members}
            
            # Remove connection
            del self.active_connections[connection_id]
            del self.connection_metadata[connection_id]
            
            self.log_event("websocket_disconnected", connection_id=connection_id)
    
    async def send_personal_message(self, message: str, connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                self.log_error(e, operation="send_personal_message", connection_id=connection_id)
                # Remove broken connection
                self.disconnect(websocket)
    
    async def send_json_message(self, data: dict, connection_id: str):
        """Send a JSON message to a specific connection."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_json(data)
            except Exception as e:
                self.log_error(e, operation="send_json_message", connection_id=connection_id)
                self.disconnect(websocket)
    
    async def broadcast_message(self, message: str):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                self.log_error(e, operation="broadcast_message", connection_id=connection_id)
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_json(self, data: dict):
        """Broadcast a JSON message to all connected clients."""
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(data)
            except Exception as e:
                self.log_error(e, operation="broadcast_json", connection_id=connection_id)
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)
    
    def join_room(self, connection_id: str, room_id: str):
        """Add a connection to a room."""
        if connection_id in self.active_connections:
            if room_id not in self.rooms:
                self.rooms[room_id] = set()
            self.rooms[room_id].add(connection_id)
            
            self.log_event("websocket_joined_room", connection_id=connection_id, room_id=room_id)
    
    def leave_room(self, connection_id: str, room_id: str):
        """Remove a connection from a room."""
        if room_id in self.rooms:
            self.rooms[room_id].discard(connection_id)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
            
            self.log_event("websocket_left_room", connection_id=connection_id, room_id=room_id)
    
    async def send_to_room(self, message: str, room_id: str):
        """Send a message to all connections in a room."""
        if room_id not in self.rooms:
            return
        
        disconnected = []
        for connection_id in self.rooms[room_id].copy():
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    self.log_error(e, operation="send_to_room", connection_id=connection_id, room_id=room_id)
                    disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def send_json_to_room(self, data: dict, room_id: str):
        """Send a JSON message to all connections in a room."""
        if room_id not in self.rooms:
            return
        
        disconnected = []
        for connection_id in self.rooms[room_id].copy():
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    await websocket.send_json(data)
                except Exception as e:
                    self.log_error(e, operation="send_json_to_room", connection_id=connection_id, room_id=room_id)
                    disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_room_members(self, room_id: str) -> List[str]:
        """Get list of connection IDs in a room."""
        return list(self.rooms.get(room_id, set()))
    
    def get_connection_metadata(self, connection_id: str) -> Optional[Dict]:
        """Get metadata for a connection."""
        return self.connection_metadata.get(connection_id)
    
    def is_connected(self, connection_id: str) -> bool:
        """Check if a connection is active."""
        return connection_id in self.active_connections
    
    async def send_agent_response(self, agent_id: str, user_id: str, response_data: dict):
        """Send agent response to specific user."""
        connection_id = f"agent_{agent_id}_{user_id}"
        message = {
            "type": "agent_response",
            "agent_id": agent_id,
            "data": response_data,
            "timestamp": response_data.get("timestamp")
        }
        await self.send_json_message(message, connection_id)
    
    async def broadcast_paper_update(self, paper_data: dict):
        """Broadcast paper update to all connected clients."""
        message = {
            "type": "paper_update",
            "data": paper_data,
            "timestamp": paper_data.get("updated_at")
        }
        await self.broadcast_json(message)
    
    async def send_system_notification(self, notification_data: dict, user_id: Optional[str] = None):
        """Send system notification to user or broadcast."""
        message = {
            "type": "system_notification",
            "data": notification_data,
            "timestamp": notification_data.get("timestamp")
        }
        
        if user_id:
            # Send to specific user (find their connections)
            user_connections = [
                conn_id for conn_id, metadata in self.connection_metadata.items()
                if metadata.get("user_id") == user_id
            ]
            for connection_id in user_connections:
                await self.send_json_message(message, connection_id)
        else:
            # Broadcast to all
            await self.broadcast_json(message)
    
    async def handle_multi_agent_collaboration(self, collaboration_id: str, participants: List[str], update_data: dict):
        """Handle multi-agent collaboration updates."""
        room_id = f"collaboration_{collaboration_id}"
        
        # Add participants to collaboration room
        for participant in participants:
            self.join_room(participant, room_id)
        
        # Send update to collaboration room
        message = {
            "type": "collaboration_update",
            "collaboration_id": collaboration_id,
            "data": update_data,
            "timestamp": update_data.get("timestamp")
        }
        await self.send_json_to_room(message, room_id)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()