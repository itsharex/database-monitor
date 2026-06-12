"""
Prometheus 集成服务（加分项）。
支持从 Prometheus 拉取已有 Exporter 的指标数据。
"""

import logging
from typing import Dict, List, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class PrometheusService:
    """Prometheus 指标拉取服务。"""

    def __init__(self) -> None:
        settings = get_settings()
        self._url = settings.prometheus_url

    @property
    def is_enabled(self) -> bool:
        return bool(self._url)

    async def query_instant(self, promql: str) -> Optional[float]:
        """执行 PromQL 即时查询，返回单个数值。"""
        if not self._url:
            return None

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self._url}/api/v1/query",
                    params={"query": promql},
                )
                data = resp.json()
                if data.get("status") == "success":
                    results = data["data"]["result"]
                    if results:
                        return float(results[0]["value"][1])
        except Exception as e:
            logger.error("Prometheus 查询失败: %s", e)
        return None

    async def query_range(
        self, promql: str, start: str, end: str, step: str = "30s"
    ) -> List[Dict]:
        """执行 PromQL 范围查询。"""
        if not self._url:
            return []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self._url}/api/v1/query_range",
                    params={"query": promql, "start": start, "end": end, "step": step},
                )
                data = resp.json()
                if data.get("status") == "success":
                    return data["data"]["result"]
        except Exception as e:
            logger.error("Prometheus 范围查询失败: %s", e)
        return []

    async def get_mysql_metrics_from_exporter(self, instance: str) -> Dict[str, float]:
        """从 mysqld_exporter 拉取 MySQL 指标。"""
        metrics = {}
        mappings = {
            "mysql_global_status_threads_connected": "connections",
            "mysql_global_status_questions": "qps",
            "mysql_global_status_slow_queries": "slow_queries",
        }
        for promql_name, metric_name in mappings.items():
            value = await self.query_instant(f'{promql_name}{{instance="{instance}"}}')
            if value is not None:
                metrics[metric_name] = value
        return metrics


prometheus_service = PrometheusService()
