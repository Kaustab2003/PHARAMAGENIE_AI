# api/websocket.py
from fastapi import WebSocket
from typing import Dict, List, Optional
import json
import asyncio
import logging

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.logger = logging.getLogger("websocket")
        
    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.logger.info(f"Client {client_id} connected")
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            self.logger.info(f"Client {client_id} disconnected")
            
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
            
    async def broadcast(self, message: str, exclude: List[str] = None):
        exclude = exclude or []
        for client_id, connection in self.active_connections.items():
            if client_id not in exclude:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    self.logger.error(f"Error sending to {client_id}: {e}")
                    self.disconnect(client_id)

manager = ConnectionManager()

async def send_progress_update(client_id: str, progress: int, status: str, message: str):
    await manager.send_personal_message(
        json.dumps({
            "type": "progress",
            "data": {
                "progress": progress,
                "status": status,
                "message": message
            }
        }),
        client_id
    )