"""FastAPI application setup - Relay Server."""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import logging
from pydantic import BaseModel

from server.room_manager import RoomManager
from server.handlers import WebSocketHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ttRPG Dice Roller - Relay", version="0.2.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services (relay only - no game logic on server)
room_manager = RoomManager()
ws_handler = WebSocketHandler(room_manager)


class RoomSummary(BaseModel):
    """Summary of an active room exposed via REST API."""

    room_id: str
    client_count: int


class RoomListResponse(BaseModel):
    """Response payload for the active room list endpoint."""

    rooms: list[RoomSummary]


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/rooms", response_model=RoomListResponse)
async def list_rooms():
    """List active rooms that currently have connected clients."""
    rooms = [RoomSummary(**room) for room in room_manager.list_active_rooms()]
    return RoomListResponse(rooms=rooms)


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for dice roller."""
    await ws_handler.handle_connection(room_id, websocket)
