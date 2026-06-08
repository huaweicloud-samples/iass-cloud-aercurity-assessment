"""条目管理API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.audit import Item
from app.schemas.audit import ItemCreate, ItemResponse, ItemListResponse
from app.core.auth import get_current_user, RoleChecker
from app.models.audit import User

router = APIRouter(prefix="/api/v1/items", tags=["标准条目管理"])
allow_admin = RoleChecker("eval_admin")


@router.post("", response_model=ItemResponse, summary="创建标准条目")
async def create_item(
    data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin)
):
    existing = db.query(Item).filter(Item.id == data.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="条目ID已存在")
    item = Item(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=ItemListResponse, summary="获取条目列表")
async def get_items(
    section: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Item)
    if section:
        query = query.filter(Item.section == section)
    if status:
        query = query.filter(Item.status == status)
    items = query.order_by(Item.id).all()
    return ItemListResponse(total=len(items), items=items)


@router.get("/{item_id}", response_model=ItemResponse, summary="获取条目详情")
async def get_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")
    return item


@router.put("/{item_id}", response_model=ItemResponse, summary="更新条目")
async def update_item(
    item_id: str,
    data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin)
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")
    item.requirement = data.requirement
    item.section = data.section
    item.item_type = data.item_type
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", summary="删除条目")
async def delete_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin)
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")
    db.delete(item)
    db.commit()
    return {"code": 200, "message": "删除成功"}
