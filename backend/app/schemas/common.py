"""
通用响应模式。
"""

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一 API 响应格式。"""

    code: int = 0
    message: str = "success"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应。"""

    total: int
    page: int
    page_size: int
    items: List[T]


class TokenResponse(BaseModel):
    """登录令牌响应。"""

    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
