import asyncio
import json

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket.connection_manager import manager
from app.services.incidents.live_events import INCIDENTS_CHANNEL

router = APIRouter(tags=["WebSocket"])

# ── Redis connection (async) ──────────────────────────────────────────────────
# Matches the same broker URL used by Celery in celery_app.py
REDIS_URL = "redis://localhost:6379/0"
INCIDENTS_CONNECTION_KEY = "__incidents__"


@router.websocket("/ws/agent-trace/{run_id}")
async def agent_trace_websocket(websocket: WebSocket, run_id: str):
    """
    WebSocket endpoint that streams live LangGraph agent step events
    to the browser as the Celery worker processes each node.

    Event shape sent to the client:
    {
        "event":      "step_update" | "run_complete" | "run_failed" | "ping",
        "run_id":     "42",
        "step_index": 0-3,
        "step_name":  "detection" | "reasoning" | "parser" | "reporting",
        "status":     "running" | "done" | "error",
        "message":    "Human readable status string",
        "payload":    {}   # optional extra data
    }
    """
    await manager.connect(run_id, websocket)

    # Subscribe to the Redis pub/sub channel for this run
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()
    channel = f"agent_trace:{run_id}"
    await pubsub.subscribe(channel)

    try:
        # Send immediate acknowledgement so the frontend knows it's connected
        await websocket.send_json({
            "event":   "connected",
            "run_id":  run_id,
            "message": f"Watching agent run #{run_id}",
        })

        # Poll Redis for messages and forward to the WebSocket client
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )

            if message and message.get("type") == "message":
                try:
                    data = json.loads(message["data"])
                    await manager.broadcast(run_id, data)

                    # Stop listening once the run finishes
                    if data.get("event") in ("run_complete", "run_failed"):
                        break
                except (json.JSONDecodeError, Exception):
                    pass

            # Keep the connection alive with a heartbeat every second
            try:
                await websocket.send_json({"event": "ping"})
            except Exception:
                break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass

    finally:
        await pubsub.unsubscribe(channel)
        await redis_client.aclose()
        manager.disconnect(run_id, websocket)


@router.websocket("/ws/incidents")
async def incidents_websocket(websocket: WebSocket):
    await manager.connect(INCIDENTS_CONNECTION_KEY, websocket)

    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(INCIDENTS_CHANNEL)

    try:
        await websocket.send_json({
            "event": "connected",
            "channel": INCIDENTS_CHANNEL,
            "message": "Watching incidents feed",
        })

        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )

            if message and message.get("type") == "message":
                try:
                    data = json.loads(message["data"])
                    await manager.broadcast(INCIDENTS_CONNECTION_KEY, data)
                except (json.JSONDecodeError, Exception):
                    pass

            try:
                await websocket.send_json({"event": "ping"})
            except Exception:
                break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass

    finally:
        await pubsub.unsubscribe(INCIDENTS_CHANNEL)
        await redis_client.aclose()
        manager.disconnect(INCIDENTS_CONNECTION_KEY, websocket)
