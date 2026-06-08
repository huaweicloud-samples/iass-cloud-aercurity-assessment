"""材料管理API - 上传/填报/版本"""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import Material, Item, Base_, User
from app.schemas.audit import MaterialResponse, MaterialUpload
from app.core.auth import get_current_user, RoleChecker, require_base_access
from app.services.ocr_service import ocr_service
from config import UPLOAD_DIR, MAX_FILE_SIZE

router = APIRouter(prefix="/api/v1/materials", tags=["材料管理"])
allow_base_user = RoleChecker("base_user")


@router.post("/upload", response_model=MaterialResponse, summary="上传申报材料")
async def upload_material(
    item_id: str = Form(...),
    base_id: str = Form(...),
    material_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_base_user)
):
    require_base_access(base_id, current_user)

    # 校验条目和基地
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")
    base = db.query(Base_).filter(Base_.id == base_id).first()
    if not base:
        raise HTTPException(status_code=404, detail="基地不存在")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超限")

    # 保存文件
    ext = os.path.splitext(file.filename)[1]
    file_dir = os.path.join(UPLOAD_DIR, "base_documents", base_id, item_id)
    os.makedirs(file_dir, exist_ok=True)

    # 获取当前版本号
    existing = db.query(Material).filter(
        Material.item_id == item_id,
        Material.base_id == base_id,
        Material.material_type == material_type
    ).order_by(Material.version.desc()).first()
    version = (existing.version + 1) if existing else 1

    file_path = os.path.join(file_dir, f"{material_type}_v{version}{ext}")
    with open(file_path, "wb") as f:
        f.write(content)

    # OCR提取文本
    content_text = ""
    try:
        content_text = ocr_service.recognize(file_path)
    except Exception as e:
        pass  # OCR失败不阻断上传

    material = Material(
        item_id=item_id,
        base_id=base_id,
        material_type=material_type,
        file_format=ext.replace(".", ""),
        file_path=file_path,
        content_text=content_text,
        version=version
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.post("/fill", response_model=MaterialResponse, summary="填报材料文本内容")
async def fill_material(
    data: MaterialUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_base_user)
):
    require_base_access(data.base_id, current_user)

    existing = db.query(Material).filter(
        Material.item_id == data.item_id,
        Material.base_id == data.base_id,
        Material.material_type == data.material_type
    ).order_by(Material.version.desc()).first()
    version = (existing.version + 1) if existing else 1

    material = Material(
        item_id=data.item_id,
        base_id=data.base_id,
        material_type=data.material_type,
        content_text=data.content_text,
        version=version
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.get("/{item_id}/{base_id}", summary="获取材料列表")
async def get_materials(
    item_id: str,
    base_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_base_access(base_id, current_user)
    materials = db.query(Material).filter(
        Material.item_id == item_id,
        Material.base_id == base_id
    ).order_by(Material.version.desc()).all()
    return {"total": len(materials), "materials": [MaterialResponse.model_validate(m) for m in materials]}
