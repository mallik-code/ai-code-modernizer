import asyncio
import json
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from utils.logger import setup_logger
import logging
from datetime import datetime
import os
from pathlib import Path


logger = setup_logger(__name__)
# The websocket messages will be logged through the unified logger
websocket_logger = logger

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, migration_id: str):
        await websocket.accept()
        if migration_id not in self.active_connections:
            self.active_connections[migration_id] = set()
        self.active_connections[migration_id].add(websocket)
        logger.info(f"WebSocket connected for migration {migration_id}")
        
        # Log the connection event
        websocket_logger.info(f"[{migration_id}] CONNECTION: WebSocket connected")

    def disconnect(self, websocket: WebSocket, migration_id: str):
        if migration_id in self.active_connections:
            self.active_connections[migration_id].discard(websocket)
            if not self.active_connections[migration_id]:  # Remove empty sets
                del self.active_connections[migration_id]
            logger.info(f"WebSocket disconnected for migration {migration_id}")
            
            # Log the disconnection event
            websocket_logger.info(f"[{migration_id}] DISCONNECTION: WebSocket disconnected")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, migration_id: str):
        if migration_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[migration_id]:
                try:
                    # Log the message to the file
                    try:
                        message_data = json.loads(message)
                        log_msg = f"[{migration_id}] {message_data.get('type', 'unknown')}: {message_data.get('message', 'No message')}"
                        websocket_logger.info(log_msg)
                    except json.JSONDecodeError:
                        # If message is not valid JSON, log it as-is
                        websocket_logger.info(f"[{migration_id}] RAW: {message}")
                    
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected clients
            for connection in disconnected:
                self.active_connections[migration_id].discard(connection)
            
            if not self.active_connections[migration_id]:
                del self.active_connections[migration_id]

manager = ConnectionManager()