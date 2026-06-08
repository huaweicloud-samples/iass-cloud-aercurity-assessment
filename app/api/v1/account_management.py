"""账户管理API - 基地管理 + 用户管理"""
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import User, Base_
from app.schemas.audit import BaseCreate, BaseResponse, UserResponse
from app.core.auth import get_current_user, RoleChecker, hash_password

allow_eval_admin = RoleChecker("eval_admin")

# ============ 基地管理 ============
router_base = APIRouter(prefix="/api/v1/bases", tags=["基地管理"])


@router_base.post("", summary="创建基地")
async def create_base(
    data: BaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin)
):
    existing = db.query(Base_).filter(Base_.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="基地编码已存在")
    base = Base_(name=data.name, code=data.code)
    db.add(base)
    db.commit()
    db.refresh(base)
    return BaseResponse.model_validate(base)


@router_base.get("", summary="获取基地列表")
async def get_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 管理员和审核专家可查看所有基地，基地用户只能查看关联基地
    if current_user.role in ("sys_admin", "eval_admin", "auditor"):
        bases = db.query(Base_).all()
    else:
        assigned = json.loads(current_user.assigned_bases or "[]")
        bases = db.query(Base_).filter(Base_.id.in_(assigned)).all() if assigned else []
    result = []
    for b in bases:
        admin_ids = json.loads(b.admin_users or "[]")
        admin_names = []
        for uid in admin_ids:
            u = db.query(User).filter(User.id == uid).first()
            if u:
                admin_names.append(u.username)
        result.append({
            **BaseResponse.model_validate(b).model_dump(),
            "admin_user_names": admin_names,
        })
    return {"total": len(result), "bases": result}


@router_base.get("/{base_id}", summary="获取基地详情")
async def get_base(
    base_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    base = db.query(Base_).filter(Base_.id == base_id).first()
    if not base:
        raise HTTPException(status_code=404, detail="基地不存在")
    return BaseResponse.model_validate(base)


class BaseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    declaration_status: Optional[str] = None


@router_base.put("/{base_id}", summary="更新基地")
async def update_base(
    base_id: str,
    data: BaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin)
):
    base = db.query(Base_).filter(Base_.id == base_id).first()
    if not base:
        raise HTTPException(status_code=404, detail="基地不存在")
    if data.name is not None:
        base.name = data.name
    if data.code is not None:
        base.code = data.code
    if data.declaration_status is not None:
        base.declaration_status = data.declaration_status
    base.updated_at = datetime.now()
    db.commit()
    db.refresh(base)
    return BaseResponse.model_validate(base)


@router_base.delete("/{base_id}", summary="删除基地")
async def delete_base(
    base_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin)
):
    base = db.query(Base_).filter(Base_.id == base_id).first()
    if not base:
        raise HTTPException(status_code=404, detail="基地不存在")
    db.delete(base)
    db.commit()
    return {"code": 200, "message": "删除成功"}


# ============ 用户管理 ============
router_user = APIRouter(prefix="/api/v1/users", tags=["用户管理"])


class UserCreateAdmin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(default="base_user")
    assigned_bases: List[str] = Field(default_factory=list, description="关联基地ID列表，基地用户必填，管理员角色可为空")


class UserUpdateAdmin(BaseModel):
    role: Optional[str] = None
    assigned_bases: Optional[List[str]] = None
    is_active: Optional[bool] = None


@router_user.post("", summary="创建用户(关联基地)")
async def create_user(
    data: UserCreateAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin)
):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 基地用户必须关联基地，管理员角色不需要
    if data.role == "base_user" and not data.assigned_bases:
        raise HTTPException(status_code=400, detail="基地申报人员必须关联至少一个基地")

    # 校验关联基地存在
    for bid in data.assigned_bases:
        base = db.query(Base_).filter(Base_.id == bid).first()
        if not base:
            raise HTTPException(status_code=400, detail=f"基地 {bid} 不存在")

    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        role=data.role,
        assigned_bases=json.dumps(data.assigned_bases),
    )
    db.add(user)
    db.flush()

    # 将用户添加到基地的admin_users
    for bid in data.assigned_bases:
        base = db.query(Base_).filter(Base_.id == bid).first()
        if base:
            admin_ids = json.loads(base.admin_users or "[]")
            if user.id not in admin_ids:
                admin_ids.append(user.id)
                base.admin_users = json.dumps(admin_ids)

    db.commit()
    db.refresh(user)
    return _user_with_bases(user, db)


@router_user.get("", summary="获取用户列表")
async def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin)
):
    users = db.query(User).all()
    return {"total": len(users), "users": [_user_with_bases(u, db) for u in users]}


@router_user.get("/{user_id}", summary="获取用户详情")
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return _user_with_bases(user, db)


@router_user.put("/{user_id}", summary="更新用户")
async def update_user(
    user_id: str,
    data: UserUpdateAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.assigned_bases is not None:
        # 校验基地存在
        for bid in data.assigned_bases:
            base = db.query(Base_).filter(Base_.id == bid).first()
            if not base:
                raise HTTPException(status_code=400, detail=f"基地 {bid} 不存在")

        old_bases = set(json.loads(user.assigned_bases or "[]"))
        new_bases = set(data.assigned_bases)

        # 从旧基地移除
        for bid in old_bases - new_bases:
            base = db.query(Base_).filter(Base_.id == bid).first()
            if base:
                admin_ids = json.loads(base.admin_users or "[]")
                if user.id in admin_ids:
                    admin_ids.remove(user.id)
                    base.admin_users = json.dumps(admin_ids)

        # 添加到新基地
        for bid in new_bases - old_bases:
            base = db.query(Base_).filter(Base_.id == bid).first()
            if base:
                admin_ids = json.loads(base.admin_users or "[]")
                if user.id not in admin_ids:
                    admin_ids.append(user.id)
                    base.admin_users = json.dumps(admin_ids)

        user.assigned_bases = json.dumps(data.assigned_bases)

    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)
    return _user_with_bases(user, db)


@router_user.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    # 从所有基地移除
    old_bases = json.loads(user.assigned_bases or "[]")
    for bid in old_bases:
        base = db.query(Base_).filter(Base_.id == bid).first()
        if base:
            admin_ids = json.loads(base.admin_users or "[]")
            if user.id in admin_ids:
                admin_ids.remove(user.id)
                base.admin_users = json.dumps(admin_ids)

    db.delete(user)
    db.commit()
    return {"code": 200, "message": "删除成功"}


def _user_with_bases(user: User, db: Session) -> dict:
    """用户信息附带基地名称"""
    base_ids = json.loads(user.assigned_bases or "[]")
    base_names = []
    for bid in base_ids:
        b = db.query(Base_).filter(Base_.id == bid).first()
        if b:
            base_names.append({"id": b.id, "name": b.name, "code": b.code})
    return {
        **UserResponse.model_validate(user).model_dump(),
        "base_details": base_names,
    }
