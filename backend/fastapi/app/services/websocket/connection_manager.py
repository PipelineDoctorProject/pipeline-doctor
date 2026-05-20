import json
from collections import defaultdict
from fastapi import WebSocket
import asyncio


class ConnectionManager:
    """
    Manages active WebSocket connections keyed by agent_run_id.
    Multiple browser tabs can watch the same run simultaneously.
    """

    def __init__(self):
        # { run_id: [WebSocket, WebSocket, ...] }
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, run_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections[run_id].append(websocket)

    def disconnect(self, run_id: str, websocket: WebSocket):
        connections = self._connections.get(run_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self._connections.pop(run_id, None)

    async def broadcast(self, run_id: str, event: dict):
        """Send a JSON event to all clients watching this run."""
        message = json.dumps(event)
        dead = []

        for ws in list(self._connections.get(run_id, [])):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(run_id, ws)

    def active_run_ids(self) -> list[str]:
        return list(self._connections.keys())


# Singleton — imported everywhere in the app
manager = ConnectionManager()
