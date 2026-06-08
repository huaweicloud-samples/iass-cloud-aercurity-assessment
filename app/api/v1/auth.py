"""认证API - 登录/注册/Token"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import User, Base_
from app.schemas.audit import UserLogin, UserCreate, UserResponse, TokenResponse
from app.core.auth import (
    hash_password, verify_password, create_access_token, get_current_user
)

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已禁用")

    token = create_access_token({
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
    })
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )


@router.post("/register", response_model=UserResponse, summary="用户注册(需关联基地)")
async def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    import json
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
        assigned_bases=json.dumps(data.assigned_bases)
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
    return user


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
