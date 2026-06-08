import os
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Template
from app.schemas.document import TemplateResponse, TemplateListResponse
from app.utils.document_handler import DocumentHandler
from config import TEMPLATE_DIR, MAX_FILE_SIZE

router = APIRouter(prefix="/api/documents/templates", tags=["模板管理"])


@router.post("/upload", response_model=TemplateResponse, summary="上传Word标准模板")
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db)
):
    """管理员上传标准.docx格式Word申报模板"""
    # 校验文件扩展名
    if not DocumentHandler.validate_file_extension(file.filename):
        raise HTTPException(status_code=400, detail="不支持的文件格式，仅允许.docx/.xlsx/.xls文件")

    # 校验文件大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制({MAX_FILE_SIZE // 1024 // 1024}MB)")

    # 生成唯一文件名
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(TEMPLATE_DIR, unique_filename)

    # 保存文件
    with open(file_path, "wb") as f:
        f.write(content)

    # 创建数据库记录
    template = Template(
        name=name,
        document_type=document_type,
        file_path=file_path,
        status="active"
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    return template


@router.get("", response_model=TemplateListResponse, summary="获取全部模板列表")
async def get_templates(
    status: str = None,
    db: Session = Depends(get_db)
):
    """获取全部模板列表，支持按状态筛选"""
    query = db.query(Template)
    if status:
        query = query.filter(Template.status == status)
    templates = query.order_by(Template.created_at.desc()).all()
    return TemplateListResponse(total=len(templates), templates=templates)


@router.get("/{template_id}", response_model=TemplateResponse, summary="获取指定模板详细信息")
async def get_template(template_id: int, db: Session = Depends(get_db)):
    """获取指定模板详细信息"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.delete("/{template_id}", response_model=TemplateResponse, summary="禁用指定模板")
async def disable_template(template_id: int, db: Session = Depends(get_db)):
    """禁用指定模板（软删除）"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    template.status = "inactive"
    template.updated_at = datetime.now()
    db.commit()
    db.refresh(template)
    return template
