"""
用户相关模式。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    """用户登录请求。"""

    username: str
    password: str


class UserCreate(BaseModel):
    """创建用户请求。"""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)
    email: str = ""
    role: str = "viewer"


class UserResponse(BaseModel):
    """用户响应。"""

    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
