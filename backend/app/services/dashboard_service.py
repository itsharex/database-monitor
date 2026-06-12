"""
大屏数据聚合服务。
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select

from app.database import AsyncSessionLocal
from app.models.alert import Alert
from app.models.instance import DatabaseInstance
from app.schemas.metrics import DashboardKPI, TreemapItem
from app.services.alert_service import alert_service
from app.services.analytics_service import analytics_service
from app.services.collector_service import collector_service
from app.services.influxdb_service import influxdb_service


class DashboardService:
    """大屏 KPI 与热力图数据聚合。"""

    async def get_kpi(self) -> DashboardKPI:
        """获取顶部 KPI 卡片数据。"""
        async with AsyncSessionLocal() as session:
            total = await session.execute(
                select(func.count(DatabaseInstance.id)).where(
                    DatabaseInstance.is_enabled == True  # noqa: E712
                )
            )
            total_count = total.scalar() or 0

            abnormal = await session.execute(
                select(func.count(DatabaseInstance.id)).where(
                    DatabaseInstance.status.in_(["warning", "critical", "offline"])
                )
            )
            abnormal_count = abnormal.scalar() or 0

        # 聚合实时指标
        total_qps = 0.0
        total_connections = 0.0
        healthy_count = 0

        for inst_id, data in collector_service.latest_metrics.items():
            metrics = data.get("metrics", {})
            total_qps += metrics.get("qps", 0)
            total_connections += metrics.get("connections", 0)
            if data.get("status") == "normal":
                healthy_count += 1

        if total_count == 0:
            health_score = 100.0
            avg_qps = 0.0
        else:
            instance_count = max(len(collector_service.latest_metrics), 1)
            health_score = (healthy_count / instance_count) * 100
            avg_qps = total_qps / instance_count

        today_alerts = await alert_service.get_today_alert_count()
        trends = await analytics_service.get_kpi_trends()

        return DashboardKPI(
            total_instances=total_count,
            abnormal_instances=abnormal_count,
            avg_qps=round(avg_qps, 2),
            total_connections=round(total_connections, 0),
            today_alerts=today_alerts,
            health_score=round(health_score, 1),
            avg_qps_trend=trends["avg_qps_trend"],
            total_connections_trend=trends["total_connections_trend"],
            today_alerts_trend=trends["today_alerts_trend"],
            health_score_trend=trends["health_score_trend"],
        )

    async def get_treemap_data(self) -> List[TreemapItem]:
        """获取底部热力图/矩形树图数据。"""
        items = []
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DatabaseInstance).where(DatabaseInstance.is_enabled == True)  # noqa: E712
            )
            instances = result.scalars().all()

        for inst in instances:
            cached = collector_service.latest_metrics.get(inst.id, {})
            metrics = cached.get("metrics", {})
            items.append(
                TreemapItem(
                    name=inst.name,
                    instance_id=inst.id,
                    value=metrics.get("qps", 0),
                    cpu_usage=metrics.get("cpu_usage", 0),
                    status=inst.status,
                )
            )
        return items

    async def get_instance_list(
        self, status_filter: Optional[str] = None, group_id: Optional[int] = None
    ) -> list:
        """获取实例列表（含实时指标预览）。"""
        async with AsyncSessionLocal() as session:
            query = select(DatabaseInstance).where(DatabaseInstance.is_enabled == True)  # noqa: E712
            if status_filter and status_filter != "all":
                query = query.where(DatabaseInstance.status == status_filter)
            if group_id:
                query = query.where(DatabaseInstance.group_id == group_id)
            result = await session.execute(query)
            instances = result.scalars().all()

        items = []
        for inst in instances:
            cached = collector_service.latest_metrics.get(inst.id, {})
            metrics = cached.get("metrics", {})
            items.append({
                "id": inst.id,
                "name": inst.name,
                "db_type": inst.db_type,
                "status": inst.status,
                "group_id": inst.group_id,
                "connections": metrics.get("connections", 0),
                "qps": metrics.get("qps", 0),
                "cpu_usage": metrics.get("cpu_usage", 0),
                "host": inst.host,
                "port": inst.port,
            })
        return items


dashboard_service = DashboardService()
