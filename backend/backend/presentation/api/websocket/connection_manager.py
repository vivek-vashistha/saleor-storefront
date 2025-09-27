"""WebSocket connection manager for real-time communication."""

import json
import logging
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("conversational_commerce.websocket")


class ConnectionManager:
    """Manages WebSocket connections for real-time chat communication."""

    def __init__(self):
        """Initialize the connection manager."""
        # Active connections by session_id
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """Accept a new WebSocket connection for a session.

        Args:
            websocket: The WebSocket connection
            session_id: The chat session ID
        """
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        
        # Check if this websocket is already connected (prevent duplicates)
        if websocket in self.active_connections[session_id]:
            logger.warning(f"WebSocket already connected for session {session_id}, skipping duplicate")
            return
        
        # More aggressive duplicate prevention - check by websocket object identity
        for existing_ws in self.active_connections[session_id]:
            if existing_ws is websocket:
                logger.warning(f"WebSocket object already exists for session {session_id}, skipping duplicate")
                return
        
        # Clean up any unhealthy connections before adding new one
        healthy_connections = []
        for conn in self.active_connections[session_id]:
            if self.is_connection_healthy(conn):
                healthy_connections.append(conn)
            else:
                logger.info(f"Removing unhealthy connection for session {session_id}")
        
        self.active_connections[session_id] = healthy_connections
        
        # Limit connections per session to prevent too many duplicates
        MAX_CONNECTIONS_PER_SESSION = 2  # Allow max 2 connections per session
        
        if len(self.active_connections[session_id]) >= MAX_CONNECTIONS_PER_SESSION:
            logger.warning(f"Maximum connections ({MAX_CONNECTIONS_PER_SESSION}) reached for session {session_id}")
            logger.warning(f"Closing oldest connection to make room for new one")
            
            # Close the oldest connection (first in list)
            oldest_connection = self.active_connections[session_id][0]
            try:
                await oldest_connection.close(code=1000, reason="Too many connections")
            except Exception as e:
                logger.warning(f"Error closing oldest connection: {e}")
            
            # Remove the oldest connection
            self.active_connections[session_id].pop(0)
        
        # Add the new connection
        self.active_connections[session_id].append(websocket)
        
        # Log warning if multiple connections detected
        connection_count = len(self.active_connections[session_id])
        if connection_count > 1:
            logger.warning(f"Multiple WebSocket connections detected for session {session_id}: {connection_count} connections")
            logger.warning(f"This may cause duplicate messages. Consider checking frontend connection logic.")
        
        logger.info(f"WebSocket connected for session {session_id}. Total connections: {connection_count}")

    def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
            session_id: The chat session ID
        """
        if session_id in self.active_connections:
            try:
                # Remove the specific websocket
                self.active_connections[session_id].remove(websocket)
                
                # Log remaining connections
                remaining_count = len(self.active_connections[session_id])
                logger.info(f"WebSocket disconnected for session {session_id}. Remaining connections: {remaining_count}")
                
                # Clean up empty session
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
                    logger.info(f"Session {session_id} has no more connections, cleaned up")
                    
            except ValueError:
                # WebSocket was already removed or not in the list
                logger.warning(f"WebSocket was not found in active connections for session {session_id}")
                # Clean up empty session if it exists
                if session_id in self.active_connections and not self.active_connections[session_id]:
                    del self.active_connections[session_id]
                    logger.info(f"Cleaned up empty session {session_id}")
        else:
            logger.warning(f"Session {session_id} not found in active connections during disconnect")

    def is_connection_healthy(self, websocket: WebSocket) -> bool:
        """Check if a WebSocket connection is still healthy.
        
        Args:
            websocket: The WebSocket connection to check
            
        Returns:
            True if the connection is healthy, False otherwise
        """
        try:
            # Check if the connection has a client_state attribute and if it's disconnected
            if hasattr(websocket, 'client_state'):
                return websocket.client_state != websocket.client_state.DISCONNECTED
            return True
        except Exception:
            return False

    async def send_personal_message(self, message: dict, session_id: str) -> None:
        """Send a message to all connections for a specific session.

        Args:
            message: The message to send
            session_id: The chat session ID
        """
        logger.info(f"[WEBSOCKET_PERSONAL] Sending personal message to session {session_id}: {message.get('type', 'unknown')}")
        logger.info(f"[WEBSOCKET_PERSONAL] Active connections for session {session_id}: {len(self.active_connections.get(session_id, []))}")
        
        if session_id in self.active_connections:
            disconnected_connections = []
            for i, connection in enumerate(self.active_connections[session_id]):
                try:
                    # Check if connection is still healthy before sending
                    if not self.is_connection_healthy(connection):
                        logger.warning(f"[WEBSOCKET_PERSONAL] Connection {i+1} is not healthy, removing")
                        disconnected_connections.append(connection)
                        continue
                    
                    logger.info(f"[WEBSOCKET_PERSONAL] Sending to connection {i+1}/{len(self.active_connections[session_id])}")
                    # Ensure proper UTF-8 encoding for Unicode characters
                    json_message = json.dumps(message, ensure_ascii=False)
                    await connection.send_text(json_message)
                    logger.info(f"[WEBSOCKET_PERSONAL] Successfully sent message to connection {i+1}")
                except Exception as e:
                    logger.warning(f"[WEBSOCKET_PERSONAL] Failed to send message to WebSocket connection {i+1}: {e}")
                    disconnected_connections.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected_connections:
                logger.info(f"[WEBSOCKET_PERSONAL] Removing disconnected connection")
                self.disconnect(connection, session_id)
        else:
            logger.warning(f"[WEBSOCKET_PERSONAL] No active connections found for session {session_id}")

    async def send_tool_call_update(self, session_id: str, tool_name: str, status: str, data: dict = None) -> None:
        """Send a tool call update to the frontend.

        Args:
            session_id: The chat session ID
            tool_name: The name of the tool being called
            status: The status of the tool call (started, completed, error)
            data: Additional data about the tool call
        """
        message = {
            "type": "tool_call_update",
            "tool_name": tool_name,
            "status": status,
            "data": data or {},
            "timestamp": self._get_timestamp()
        }
        await self.send_personal_message(message, session_id)

    async def send_thinking_update(self, session_id: str, thinking: str) -> None:
        """Send a thinking update to the frontend.

        Args:
            session_id: The chat session ID
            thinking: The current thinking/processing status
        """
        message = {
            "type": "thinking_update",
            "thinking": thinking,
            "timestamp": self._get_timestamp()
        }
        await self.send_personal_message(message, session_id)

    async def send_message_chunk(self, session_id: str, chunk: str, is_final: bool = False) -> None:
        """Send a message chunk to the frontend.

        Args:
            session_id: The chat session ID
            chunk: The message chunk
            is_final: Whether this is the final chunk
        """
        logger.info(f"[WEBSOCKET_CHUNK] Sending message chunk for session {session_id}: chunk='{chunk[:50]}...', is_final={is_final}")
        logger.info(f"[WEBSOCKET_CHUNK] Active connections for session {session_id}: {len(self.active_connections.get(session_id, []))}")
        
        message = {
            "type": "message_chunk",
            "chunk": chunk,
            "is_final": is_final,
            "timestamp": self._get_timestamp()
        }
        
        logger.info(f"[WEBSOCKET_CHUNK] Message to send: {message}")
        await self.send_personal_message(message, session_id)
        logger.info(f"[WEBSOCKET_CHUNK] Message chunk sent successfully for session {session_id}")

    async def send_error(self, session_id: str, error_message: str) -> None:
        """Send an error message to the frontend.

        Args:
            session_id: The chat session ID
            error_message: The error message
        """
        message = {
            "type": "error",
            "error": error_message,
            "timestamp": self._get_timestamp()
        }
        await self.send_personal_message(message, session_id)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def get_connection_count(self, session_id: str) -> int:
        """Get the number of active connections for a session.

        Args:
            session_id: The chat session ID

        Returns:
            The number of active connections
        """
        return len(self.active_connections.get(session_id, []))


# Global connection manager instance
manager = ConnectionManager()
