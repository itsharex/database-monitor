"""
监控指标相关模式。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MetricPoint(BaseModel):
    """单个指标数据点。"""

    timestamp: datetime
    value: float


class MetricSeries(BaseModel):
    """指标时间序列。"""

    metric_name: str
    points: List[MetricPoint]


class InstanceMetrics(BaseModel):
    """实例当前指标快照。"""

    instance_id: int
    instance_name: str
    db_type: str
    status: str
    metrics: Dict[str, float]
    collected_at: datetime


class DashboardKPI(BaseModel):
    """大屏 KPI 数据。"""

    total_instances: int
    abnormal_instances: int
    avg_qps: float
    total_connections: float
    today_alerts: int
    health_score: float
    # 环比趋势（百分比变化）
    total_instances_trend: float = 0.0
    abnormal_instances_trend: float = 0.0
    avg_qps_trend: float = 0.0
    total_connections_trend: float = 0.0
    today_alerts_trend: float = 0.0
    health_score_trend: float = 0.0


class TreemapItem(BaseModel):
    """热力图/矩形树图数据项。"""

    name: str
    instance_id: int
    value: float  # QPS 或连接数
    cpu_usage: float
    status: str


class SlowQueryRecord(BaseModel):
    """慢查询记录。"""

    query_time: float
    lock_time: float
    rows_examined: int
    sql_text: str
    timestamp: datetime


class ExportRequest(BaseModel):
    """数据导出请求。"""

    instance_id: Optional[int] = None
    metric_names: List[str] = []
    start_time: datetime
    end_time: datetime
    format: str = "csv"  # csv / json
