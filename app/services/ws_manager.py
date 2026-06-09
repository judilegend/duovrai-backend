import asyncio
from typing import Any
from fastapi import WebSocket
from app.models.models import Order


class WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Any) -> None:
        disconnected: list[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


ws_manager = WebSocketManager()


def build_order_payload(order: Order) -> dict:
    return {
        "type": "order_update",
        "order": {
            "id": order.id,
            "email": order.email,
            "partner1_name": order.partner1_name,
            "partner2_name": order.partner2_name,
            "status": order.status,
            "amount": order.amount,
            "plan_type": order.plan_type,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        },
    }


def broadcast_order_payload(order: Order) -> None:
    asyncio.create_task(ws_manager.broadcast(build_order_payload(order)))
