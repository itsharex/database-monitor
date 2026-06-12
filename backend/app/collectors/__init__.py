"""数据库指标采集器。"""

from app.collectors.base import BaseCollector, CollectorResult
from app.collectors.mongodb import MongoDBCollector
from app.collectors.mysql import MySQLCollector
from app.collectors.postgresql import PostgreSQLCollector
from app.collectors.redis_collector import RedisCollector

COLLECTOR_MAP = {
    "mysql": MySQLCollector,
    "postgresql": PostgreSQLCollector,
    "redis": RedisCollector,
    "mongodb": MongoDBCollector,
}

__all__ = [
    "BaseCollector",
    "CollectorResult",
    "COLLECTOR_MAP",
    "MySQLCollector",
    "PostgreSQLCollector",
    "RedisCollector",
    "MongoDBCollector",
]
