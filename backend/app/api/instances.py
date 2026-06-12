"""
数据库实例管理 API。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, require_auth
from app.collectors import COLLECTOR_MAP
from app.database import get_db
from app.models.instance import DatabaseInstance, InstanceGroup
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.instance import (
    ConnectionTestRequest,
    ConnectionTestResponse,
    DatabaseInstanceCreate,
    DatabaseInstanceResponse,
    DatabaseInstanceUpdate,
    InstanceGroupCreate,
    InstanceGroupResponse,
)
from app.services.collector_service import collector_service
from app.utils.encryption import decrypt_password, encrypt_password

router = APIRouter(prefix="/instances", tags=["数据库实例"])


@router.get("/groups", response_model=ResponseModel[list[InstanceGroupResponse]])
async def list_groups(db: AsyncSession = Depends(get_db), _user: User = Depends(require_auth)):
    """获取所有实例分组。"""
    result = await db.execute(select(InstanceGroup))
    groups = result.scalars().all()
    return ResponseModel(data=[InstanceGroupResponse.model_validate(g) for g in groups])


@router.post("/groups", response_model=ResponseModel[InstanceGroupResponse])
async def create_group(
    data: InstanceGroupCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """创建实例分组。"""
    group = InstanceGroup(**data.model_dump())
    db.add(group)
    await db.flush()
    return ResponseModel(data=InstanceGroupResponse.model_validate(group))


@router.get("", response_model=ResponseModel[list[DatabaseInstanceResponse]])
async def list_instances(db: AsyncSession = Depends(get_db), _user: User = Depends(require_auth)):
    """获取所有数据库实例。"""
    result = await db.execute(select(DatabaseInstance))
    instances = result.scalars().all()
    items = []
    for inst in instances:
        resp = DatabaseInstanceResponse.model_validate(inst)
        cached = collector_service.latest_metrics.get(inst.id, {})
        metrics = cached.get("metrics", {})
        resp.connections = metrics.get("connections")
        resp.qps = metrics.get("qps")
        resp.cpu_usage = metrics.get("cpu_usage")
        items.append(resp)
    return ResponseModel(data=items)


@router.post("", response_model=ResponseModel[DatabaseInstanceResponse])
async def create_instance(
    data: DatabaseInstanceCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """创建数据库实例。"""
    instance = DatabaseInstance(
        name=data.name,
        db_type=data.db_type,
        host=data.host,
        port=data.port,
        username=data.username,
        encrypted_password=encrypt_password(data.password),
        database_name=data.database_name,
        max_connections=data.max_connections,
        group_id=data.group_id,
        description=data.description,
    )
    db.add(instance)
    await db.flush()
    return ResponseModel(data=DatabaseInstanceResponse.model_validate(instance))


@router.get("/{instance_id}", response_model=ResponseModel[DatabaseInstanceResponse])
async def get_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_auth),
):
    """获取单个实例详情。"""
    result = await db.execute(
        select(DatabaseInstance).where(DatabaseInstance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")
    resp = DatabaseInstanceResponse.model_validate(instance)
    cached = collector_service.latest_metrics.get(instance.id, {})
    metrics = cached.get("metrics", {})
    resp.connections = metrics.get("connections")
    resp.qps = metrics.get("qps")
    resp.cpu_usage = metrics.get("cpu_usage")
    return ResponseModel(data=resp)


@router.put("/{instance_id}", response_model=ResponseModel[DatabaseInstanceResponse])
async def update_instance(
    instance_id: int,
    data: DatabaseInstanceUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """更新数据库实例。"""
    result = await db.execute(
        select(DatabaseInstance).where(DatabaseInstance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")

    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data:
        instance.encrypted_password = encrypt_password(update_data.pop("password"))

    for key, value in update_data.items():
        setattr(instance, key, value)

    await db.flush()
    return ResponseModel(data=DatabaseInstanceResponse.model_validate(instance))


@router.delete("/{instance_id}", response_model=ResponseModel)
async def delete_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """删除数据库实例。"""
    result = await db.execute(
        select(DatabaseInstance).where(DatabaseInstance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")
    await db.delete(instance)
    return ResponseModel(message="删除成功")


@router.get("/{instance_id}/slow-queries", response_model=ResponseModel[list])
async def get_slow_queries(
    instance_id: int,
    _user: User = Depends(require_auth),
):
    """获取实例最近慢查询记录。"""
    cached = collector_service.latest_metrics.get(instance_id, {})
    return ResponseModel(data=cached.get("slow_queries", []))


@router.get("/{instance_id}/snapshot", response_model=ResponseModel[dict])
async def get_instance_snapshot(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_auth),
):
    """获取实例完整监控快照（指标 + 参数 + 建议）。"""
    result = await db.execute(
        select(DatabaseInstance).where(DatabaseInstance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")

    cached = collector_service.latest_metrics.get(instance_id, {})
    metrics = cached.get("metrics", {})

    suggestions = []
    if metrics.get("cpu_usage", 0) > 80:
        suggestions.append("CPU 使用率偏高，建议检查慢查询并优化 SQL")
    if instance.max_connections and metrics.get("connections", 0) / instance.max_connections > 0.8:
        suggestions.append(f"连接数接近上限，建议调整 max_connections（当前 {instance.max_connections}）")
    if metrics.get("slow_queries", 0) > 50:
        suggestions.append("慢查询较多，建议分析慢查询日志并添加索引")
    if not suggestions:
        suggestions.append("当前运行状态良好，暂无优化建议")

    return ResponseModel(data={
        "instance": DatabaseInstanceResponse.model_validate(instance),
        "metrics": metrics,
        "slow_queries": cached.get("slow_queries", []),
        "collected_at": cached.get("collected_at"),
        "status": cached.get("status", instance.status),
        "suggestions": suggestions,
        "params": {
            "max_connections": instance.max_connections,
            "db_type": instance.db_type,
            "host": instance.host,
            "port": instance.port,
        },
    })


@router.post("/test-connection", response_model=ResponseModel[ConnectionTestResponse])
async def test_connection(
    data: ConnectionTestRequest,
    _user: User = Depends(require_auth),
):
    """测试数据库连接。"""
    collector_cls = COLLECTOR_MAP.get(data.db_type)
    if not collector_cls:
        return ResponseModel(data=ConnectionTestResponse(
            success=False, message=f"不支持的数据库类型: {data.db_type}"
        ))

    collector = collector_cls(
        host=data.host,
        port=data.port,
        username=data.username,
        password=data.password,
        database_name=data.database_name,
    )
    success, message, latency = await collector.test_connection()
    return ResponseModel(data=ConnectionTestResponse(
        success=success, message=message, latency_ms=latency
    ))
