"""
测试配置与 fixtures。
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import create_app
from app.models.user import User
from app.utils.security import get_password_hash


@pytest_asyncio.fixture
async def test_engine():
    """创建测试数据库引擎。"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """创建测试数据库会话。"""
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def test_app(test_engine):
    """创建测试应用。"""
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    # 创建测试用户
    async with session_factory() as session:
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role="admin",
        )
        session.add(admin)
        await session.commit()

    return app


@pytest_asyncio.fixture
async def client(test_app):
    """创建异步 HTTP 测试客户端。"""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
