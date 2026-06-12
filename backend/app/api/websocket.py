"""
WebSocket 实时推送。
向前端推送实时指标和告警数据。
"""

import asyncio
import json
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.alert_service import alert_service
from app.services.collector_service import collector_service
from app.services.dashboard_service import dashboard_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """WebSocket 连接管理器。"""

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        """向所有连接广播消息。"""
        dead = set()
        for ws in self.active_connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self.active_connections -= dead


manager = ConnectionManager()


@router.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """实时指标 WebSocket 端点。"""
    await manager.connect(websocket)
    try:
        while True:
            # 每 5 秒推送一次实时数据
            kpi = await dashboard_service.get_kpi()
            instances = await dashboard_service.get_instance_list()
            treemap = await dashboard_service.get_treemap_data()

            await websocket.send_json({
                "type": "metrics_update",
                "data": {
                    "kpi": kpi.model_dump(),
                    "instances": instances,
                    "treemap": [t.model_dump() for t in treemap],
                    "latest_metrics": {
                        str(k): v for k, v in collector_service.latest_metrics.items()
                    },
                },
            })
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket 异常: %s", e)
        manager.disconnect(websocket)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """实时告警 WebSocket 端点。"""
    await manager.connect(websocket)
    try:
        while True:
            from app.database import AsyncSessionLocal
            from app.models.alert import Alert
            from sqlalchemy import select

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Alert)
                    .where(Alert.is_acknowledged == False)  # noqa: E712
                    .order_by(Alert.created_at.desc())
                    .limit(20)
                )
                alerts = result.scalars().all()

            await websocket.send_json({
                "type": "alerts_update",
                "data": [
                    {
                        "id": a.id,
                        "instance_name": a.instance_name,
                        "severity": a.severity,
                        "title": a.title,
                        "message": a.message,
                        "created_at": a.created_at.isoformat(),
                    }
                    for a in alerts
                ],
            })
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
