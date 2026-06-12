"""
采集器基类。
定义统一的采集接口与连接池管理。
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class CollectorResult:
    """采集结果。"""

    success: bool
    metrics: Dict[str, float] = field(default_factory=dict)
    slow_queries: list = field(default_factory=list)
    error_message: str = ""
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    extra_info: Dict[str, Any] = field(default_factory=dict)


class BaseCollector(ABC):
    """数据库指标采集器基类。"""

    def __init__(
        self,
        host: str,
        port: int,
        username: str = "",
        password: str = "",
        database_name: str = "",
        max_connections: int = 100,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database_name = database_name
        self.max_connections = max_connections
        self._pool: Any = None

    @abstractmethod
    async def connect(self) -> None:
        """建立连接池。"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭连接池。"""
        pass

    @abstractmethod
    async def test_connection(self) -> tuple[bool, str, Optional[float]]:
        """测试连接，返回 (成功, 消息, 延迟ms)。"""
        pass

    @abstractmethod
    async def collect(self) -> CollectorResult:
        """采集指标。"""
        pass

    async def _safe_collect(self) -> CollectorResult:
        """安全采集，捕获异常。"""
        try:
            await self.connect()
            return await self.collect()
        except Exception as e:
            logger.error("采集失败 [%s:%d]: %s", self.host, self.port, e)
            return CollectorResult(success=False, error_message=str(e))
        finally:
            await self.close()
