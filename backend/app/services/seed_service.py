"""
初始化种子数据服务。
首次启动时自动创建默认分组和可监控的演示实例。
"""

import logging
import os

from sqlalchemy import func, select

from app.database import AsyncSessionLocal
from app.models.instance import DatabaseInstance, InstanceGroup
from app.utils.encryption import encrypt_password

logger = logging.getLogger(__name__)

# 默认演示实例（Docker Compose 内网地址）
DEFAULT_GROUPS = [
    {"name": "生产环境", "group_type": "environment", "description": "生产环境数据库"},
    {"name": "基础设施", "group_type": "business", "description": "系统基础组件"},
]

DEFAULT_INSTANCES = [
    {
        "name": "系统 PostgreSQL",
        "db_type": "postgresql",
        "host": "postgres",
        "port": 5432,
        "username": "monitor",
        "password": "monitor123",
        "database_name": "db_monitor",
        "max_connections": 100,
        "group_name": "基础设施",
        "description": "监控平台配置数据库（自动注册）",
    },
    {
        "name": "系统 Redis",
        "db_type": "redis",
        "host": "redis",
        "port": 6379,
        "username": "",
        "password": "",
        "database_name": "0",
        "max_connections": 1000,
        "group_name": "基础设施",
        "description": "监控平台缓存服务（自动注册）",
    },
]


async def seed_initial_data() -> None:
    """初始化默认分组和演示实例（仅在数据库为空时执行）。"""
    # 可通过环境变量关闭自动种子数据
    if os.getenv("SEED_DEMO_DATA", "true").lower() == "false":
        logger.info("SEED_DEMO_DATA=false，跳过种子数据初始化")
        return

    async with AsyncSessionLocal() as session:
        count = await session.execute(select(func.count(DatabaseInstance.id)))
        if (count.scalar() or 0) > 0:
            logger.info("已存在监控实例，跳过种子数据")
            return

        # 创建分组
        group_map: dict[str, int] = {}
        for g in DEFAULT_GROUPS:
            group = InstanceGroup(**g)
            session.add(group)
            await session.flush()
            group_map[g["name"]] = group.id

        # 创建实例
        for inst_data in DEFAULT_INSTANCES:
            password = inst_data.pop("password")
            group_name = inst_data.pop("group_name")
            instance = DatabaseInstance(
                **inst_data,
                group_id=group_map.get(group_name),
                encrypted_password=encrypt_password(password),
                status="offline",
            )
            session.add(instance)

        await session.commit()
        logger.info("已自动注册 %d 个演示监控实例", len(DEFAULT_INSTANCES))
