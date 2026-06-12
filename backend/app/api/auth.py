"""
认证 API 路由。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.common import ResponseModel, TokenResponse
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.utils.security import create_access_token, get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=ResponseModel[TokenResponse])
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录，返回 JWT 令牌。"""
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    token = create_access_token({"sub": user.username, "role": user.role})
    return ResponseModel(data=TokenResponse(
        access_token=token,
        username=user.username,
        role=user.role,
    ))


@router.get("/me", response_model=ResponseModel[UserResponse])
async def get_me(user: User = Depends(get_current_user)):
    """获取当前用户信息。"""
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    return ResponseModel(data=UserResponse.model_validate(user))


@router.post("/users", response_model=ResponseModel[UserResponse])
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """创建新用户（管理员）。"""
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role=data.role,
    )
    db.add(user)
    await db.flush()
    return ResponseModel(data=UserResponse.model_validate(user))
