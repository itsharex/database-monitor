"""
InfluxDB 时序数据服务。
负责指标写入与查询。
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from app.config import get_settings
from app.schemas.metrics import MetricPoint, MetricSeries

logger = logging.getLogger(__name__)


class InfluxDBService:
    """InfluxDB 操作封装。"""

    def __init__(self) -> None:
        settings = get_settings()
        self._url = settings.influxdb_url
        self._token = settings.influxdb_token
        self._org = settings.influxdb_org
        self._bucket = settings.influxdb_bucket
        self._client: Optional[InfluxDBClient] = None
        self._write_api = None

    def connect(self) -> None:
        """建立 InfluxDB 连接。"""
        try:
            self._client = InfluxDBClient(
                url=self._url,
                token=self._token,
                org=self._org,
            )
            self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
            logger.info("InfluxDB 连接成功: %s", self._url)
        except Exception as e:
            logger.error("InfluxDB 连接失败: %s", e)
            self._client = None

    def close(self) -> None:
        """关闭连接。"""
        if self._client:
            self._client.close()

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    def write_metrics(
        self,
        instance_id: int,
        instance_name: str,
        db_type: str,
        metrics: Dict[str, float],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """写入一批指标数据。"""
        if not self._write_api:
            return

        ts = timestamp or datetime.now(timezone.utc)
        points = []
        for metric_name, value in metrics.items():
            point = (
                Point("db_metrics")
                .tag("instance_id", str(instance_id))
                .tag("instance_name", instance_name)
                .tag("db_type", db_type)
                .tag("metric_name", metric_name)
                .field("value", float(value))
                .time(ts)
            )
            points.append(point)

        try:
            self._write_api.write(bucket=self._bucket, org=self._org, record=points)
        except Exception as e:
            logger.error("写入 InfluxDB 失败: %s", e)

    def query_metrics(
        self,
        instance_id: int,
        metric_names: List[str],
        start: str = "-15m",
        stop: Optional[str] = None,
    ) -> List[MetricSeries]:
        """查询指标时间序列。"""
        if not self._client:
            return []

        stop_clause = f', stop: {stop}' if stop else ""
        results = []

        for metric_name in metric_names:
            flux = f'''
            from(bucket: "{self._bucket}")
              |> range(start: {start}{stop_clause})
              |> filter(fn: (r) => r["_measurement"] == "db_metrics")
              |> filter(fn: (r) => r["instance_id"] == "{instance_id}")
              |> filter(fn: (r) => r["metric_name"] == "{metric_name}")
              |> filter(fn: (r) => r["_field"] == "value")
            '''
            try:
                tables = self._client.query_api().query(flux, org=self._org)
                points = []
                for table in tables:
                    for record in table.records:
                        points.append(
                            MetricPoint(
                                timestamp=record.get_time(),
                                value=float(record.get_value()),
                            )
                        )
                results.append(MetricSeries(metric_name=metric_name, points=points))
            except Exception as e:
                logger.error("查询 InfluxDB 失败 [%s]: %s", metric_name, e)
                results.append(MetricSeries(metric_name=metric_name, points=[]))

        return results

    def query_latest_metrics(self, instance_id: int) -> Dict[str, float]:
        """查询实例最新指标值。"""
        if not self._client:
            return {}

        flux = f'''
        from(bucket: "{self._bucket}")
          |> range(start: -5m)
          |> filter(fn: (r) => r["_measurement"] == "db_metrics")
          |> filter(fn: (r) => r["instance_id"] == "{instance_id}")
          |> filter(fn: (r) => r["_field"] == "value")
          |> last()
        '''
        metrics: Dict[str, float] = {}
        try:
            tables = self._client.query_api().query(flux, org=self._org)
            for table in tables:
                for record in table.records:
                    metric_name = record.values.get("metric_name", "")
                    if metric_name:
                        metrics[metric_name] = float(record.get_value())
        except Exception as e:
            logger.error("查询最新指标失败: %s", e)
        return metrics


# 全局单例
influxdb_service = InfluxDBService()
