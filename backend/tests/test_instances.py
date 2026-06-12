"""
数据库实例管理 API 测试。
"""

import pytest


@pytest.mark.asyncio
async def test_create_and_list_instances(client):
    """测试创建和列出数据库实例。"""
    login_resp = await client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 创建实例
    create_resp = await client.post("/api/instances", json={
        "name": "测试MySQL",
        "db_type": "mysql",
        "host": "127.0.0.1",
        "port": 3306,
        "username": "root",
        "password": "test123",
        "max_connections": 100,
    }, headers=headers)
    assert create_resp.status_code == 200
    instance = create_resp.json()["data"]
    assert instance["name"] == "测试MySQL"
    assert instance["db_type"] == "mysql"

    # 列出实例
    list_resp = await client.get("/api/instances", headers=headers)
    assert list_resp.status_code == 200
    instances = list_resp.json()["data"]
    assert len(instances) >= 1


@pytest.mark.asyncio
async def test_create_group(client):
    """测试创建实例分组。"""
    login_resp = await client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/instances/groups", json={
        "name": "生产环境",
        "group_type": "environment",
        "description": "生产环境数据库",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "生产环境"
