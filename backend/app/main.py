"""
数据库监控大屏系统 - FastAPI 应用入口。
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts, auth, dashboard, export_api, instances, system, websocket
from app.config import get_settings
from app.database import init_db
from app.models.user import User
from app.services.alert_service import alert_service
from app.services.collector_service import collector_service
from app.services.influxdb_service import influxdb_service
from app.services.seed_service import seed_initial_data
from app.utils.security import get_password_hash

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def init_default_admin() -> None:
    """初始化默认管理员账号。"""
    from sqlalchemy import select
    from app.database import AsyncSessionLocal

    settings = get_settings()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.username == settings.default_admin_username)
        )
        if not result.scalar_one_or_none():
            admin = User(
                username=settings.default_admin_username,
                hashed_password=get_password_hash(settings.default_admin_password),
                role="admin",
                email="admin@db-monitor.local",
            )
            session.add(admin)
            await session.commit()
            logger.info("默认管理员已创建: %s", settings.default_admin_username)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    settings = get_settings()
    logger.info("启动 %s v%s", settings.app_name, settings.app_version)

    # 初始化数据库
    await init_db()
    await init_default_admin()
    await alert_service.init_builtin_rules()
    await seed_initial_data()

    # 连接 InfluxDB
    influxdb_service.connect()

    # 启动采集器并立即采集一次
    await collector_service.start()
    await collector_service.collect_all()

    yield

    # 清理
    await collector_service.stop()
    influxdb_service.close()
    logger.info("应用已关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例。"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="企业级数据库监控大屏系统 API",
        lifespan=lifespan,
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(auth.router, prefix="/api")
    app.include_router(instances.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")
    app.include_router(alerts.router, prefix="/api")
    app.include_router(export_api.router, prefix="/api")
    app.include_router(system.router, prefix="/api")
    app.include_router(websocket.router)

    @app.get("/api/health")
    async def health_check():
        """健康检查端点。"""
        return {
            "status": "healthy",
            "influxdb": influxdb_service.is_connected,
            "collector": collector_service._running,
        }

    return app


app = create_app()
