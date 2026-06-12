"""
监控采集调度服务。
定时并发采集所有数据库实例指标。
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors import COLLECTOR_MAP
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.instance import DatabaseInstance
from app.services.influxdb_service import influxdb_service
from app.utils.encryption import decrypt_password

logger = logging.getLogger(__name__)


class CollectorService:
    """指标采集调度器。"""

    def __init__(self) -> None:
        self._running = False
        self._task: Optional[asyncio.Task] = None
        # 缓存最新指标供 WebSocket 推送
        self.latest_metrics: Dict[int, dict] = {}
        self.collection_logs: List[dict] = []

    async def start(self) -> None:
        """启动定时采集任务。"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("采集器已启动")

    async def stop(self) -> None:
        """停止采集任务。"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("采集器已停止")

    async def _run_loop(self) -> None:
        """采集主循环。"""
        settings = get_settings()
        while self._running:
            try:
                await self.collect_all()
            except Exception as e:
                logger.error("采集循环异常: %s", e)
            await asyncio.sleep(settings.collector_interval_seconds)

    async def collect_all(self) -> None:
        """并发采集所有启用的实例。"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DatabaseInstance).where(DatabaseInstance.is_enabled == True)  # noqa: E712
            )
            instances = result.scalars().all()

        if not instances:
            return

        tasks = [self._collect_instance(inst) for inst in instances]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _collect_instance(self, instance: DatabaseInstance) -> None:
        """采集单个实例，支持重试。"""
        settings = get_settings()
        password = decrypt_password(instance.encrypted_password)
        collector_cls = COLLECTOR_MAP.get(instance.db_type)

        if not collector_cls:
            logger.warning("不支持的数据库类型: %s", instance.db_type)
            return

        for attempt in range(1, settings.collector_max_retries + 1):
            collector = collector_cls(
                host=instance.host,
                port=instance.port,
                username=instance.username,
                password=password,
                database_name=instance.database_name,
                max_connections=instance.max_connections,
            )

            result = await collector._safe_collect()

            log_entry = {
                "instance_id": instance.id,
                "instance_name": instance.name,
                "success": result.success,
                "attempt": attempt,
                "error": result.error_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.collection_logs.append(log_entry)
            # 只保留最近 500 条日志
            if len(self.collection_logs) > 500:
                self.collection_logs = self.collection_logs[-500:]

            if result.success:
                # 写入 InfluxDB
                influxdb_service.write_metrics(
                    instance_id=instance.id,
                    instance_name=instance.name,
                    db_type=instance.db_type,
                    metrics=result.metrics,
                    timestamp=result.collected_at,
                )

                # 更新缓存
                self.latest_metrics[instance.id] = {
                    "metrics": result.metrics,
                    "slow_queries": result.slow_queries,
                    "collected_at": result.collected_at.isoformat(),
                    "status": "normal",
                }

                # 更新实例状态
                await self._update_instance_status(instance.id, "normal", result.collected_at)

                # 触发告警检查
                from app.services.alert_service import alert_service
                await alert_service.check_metrics(instance, result.metrics)

                return

            logger.warning(
                "采集失败 [%s] 第 %d 次: %s",
                instance.name, attempt, result.error_message,
            )
            if attempt < settings.collector_max_retries:
                await asyncio.sleep(settings.collector_retry_delay_seconds)

        # 全部重试失败
        self.latest_metrics[instance.id] = {
            "metrics": {},
            "slow_queries": [],
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "status": "offline",
        }
        await self._update_instance_status(instance.id, "offline")

        # 连接失败告警
        from app.services.alert_service import alert_service
        await alert_service.create_connection_failure_alert(instance)

    async def _update_instance_status(
        self, instance_id: int, status: str, collected_at: Optional[datetime] = None
    ) -> None:
        """更新实例状态到关系数据库。"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DatabaseInstance).where(DatabaseInstance.id == instance_id)
            )
            instance = result.scalar_one_or_none()
            if instance:
                instance.status = status
                if collected_at:
                    instance.last_collected_at = collected_at
                await session.commit()


collector_service = CollectorService()
