"""
数据分析服务：告警统计、KPI 环比趋势。
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import func, select

from app.database import AsyncSessionLocal
from app.models.alert import Alert
from app.services.collector_service import collector_service
from app.services.influxdb_service import influxdb_service


class AnalyticsService:
    """告警统计与趋势分析。"""

    async def get_alert_stats(self, days: int = 7) -> dict:
        """按天/级别统计告警数量。"""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Alert.severity, func.count(Alert.id))
                .where(Alert.created_at >= since)
                .group_by(Alert.severity)
            )
            by_severity = {row[0]: row[1] for row in result.all()}

            # 今日 vs 昨日
            today_start = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            yesterday_start = today_start - timedelta(days=1)

            today_count = await session.execute(
                select(func.count(Alert.id)).where(Alert.created_at >= today_start)
            )
            yesterday_count = await session.execute(
                select(func.count(Alert.id)).where(
                    Alert.created_at >= yesterday_start,
                    Alert.created_at < today_start,
                )
            )

            # 最近每天告警数
            daily = []
            for i in range(days - 1, -1, -1):
                day_start = today_start - timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                cnt = await session.execute(
                    select(func.count(Alert.id)).where(
                        Alert.created_at >= day_start,
                        Alert.created_at < day_end,
                    )
                )
                daily.append({
                    "date": day_start.strftime("%m-%d"),
                    "count": cnt.scalar() or 0,
                })

        return {
            "by_severity": by_severity,
            "today": today_count.scalar() or 0,
            "yesterday": yesterday_count.scalar() or 0,
            "daily": daily,
            "total": sum(by_severity.values()),
        }

    def calc_trend_percent(self, current: float, previous: float) -> float:
        """计算环比变化百分比。"""
        if previous == 0:
            return 0.0 if current == 0 else 100.0
        return round((current - previous) / previous * 100, 1)

    async def get_kpi_trends(self) -> Dict[str, float]:
        """从 InfluxDB 历史数据计算 KPI 环比趋势（对比1小时前）。"""
        trends = {
            "avg_qps_trend": 0.0,
            "total_connections_trend": 0.0,
            "health_score_trend": 0.0,
            "today_alerts_trend": 0.0,
        }
        if not influxdb_service.is_connected:
            return trends

        current_qps = 0.0
        current_conn = 0.0
        prev_qps = 0.0
        prev_conn = 0.0
        count = 0

        for inst_id, data in collector_service.latest_metrics.items():
            metrics = data.get("metrics", {})
            current_qps += metrics.get("qps", 0)
            current_conn += metrics.get("connections", 0)

            # 查询1小时前的指标
            series = influxdb_service.query_metrics(
                inst_id, ["qps", "connections"], start="-2h", stop="-1h"
            )
            for s in series:
                if s.points:
                    val = s.points[-1].value
                    if s.metric_name == "qps":
                        prev_qps += val
                    elif s.metric_name == "connections":
                        prev_conn += val
            count += 1

        if count > 0:
            current_qps /= count
            prev_qps /= max(count, 1)
            trends["avg_qps_trend"] = self.calc_trend_percent(current_qps, prev_qps)
            trends["total_connections_trend"] = self.calc_trend_percent(current_conn, prev_conn)

        stats = await self.get_alert_stats(days=2)
        trends["today_alerts_trend"] = self.calc_trend_percent(
            stats["today"], stats["yesterday"]
        )
        return trends


analytics_service = AnalyticsService()
