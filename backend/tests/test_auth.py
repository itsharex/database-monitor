"""
认证模块单元测试。
"""

import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    """测试登录成功。"""
    resp = await client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert "access_token" in data["data"]
    assert data["data"]["username"] == "admin"


@pytest.mark.asyncio
async def test_login_failure(client):
    """测试登录失败。"""
    resp = await client.post("/api/auth/login", json={
        "username": "admin",
        "password": "wrong_password",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client):
    """测试获取当前用户信息。"""
    login_resp = await client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    token = login_resp.json()["data"]["access_token"]

    resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["username"] == "admin"
    assert resp.json()["data"]["role"] == "admin"
