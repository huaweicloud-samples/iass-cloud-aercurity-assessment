import os
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Template, ExcelTemplate, BaseDocument
from app.schemas.document import (
    ExcelTemplateResponse, ExcelTemplateListResponse, ExcelTemplateApply
)
from app.utils.document_handler import ExcelHandler
from config import TEMPLATE_DIR, UPLOAD_DIR, MAX_FILE_SIZE

router = APIRouter(prefix="/api/excel/templates", tags=["Excel模板管理"])


@router.post("/upload", response_model=ExcelTemplateResponse, summary="上传Excel数据模板")
async def upload_excel_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    """上传Excel数据模板"""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".xlsx", ".xls"]:
        raise HTTPException(status_code=400, detail="仅支持.xlsx/.xls格式文件")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制({MAX_FILE_SIZE // 1024 // 1024}MB)")

    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(TEMPLATE_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    excel_template = ExcelTemplate(
        name=name,
        file_path=file_path,
        status="active"
    )
    db.add(excel_template)
    db.commit()
    db.refresh(excel_template)

    return excel_template


@router.get("", response_model=ExcelTemplateListResponse, summary="获取Excel模板列表")
async def get_excel_templates(db: Session = Depends(get_db)):
    """获取Excel模板列表信息"""
    templates = db.query(ExcelTemplate).filter(
        ExcelTemplate.status == "active"
    ).order_by(ExcelTemplate.created_at.desc()).all()
    return ExcelTemplateListResponse(total=len(templates), templates=templates)


@router.post("/{template_id}/apply", summary="应用Excel模板批量生成申报文档")
async def apply_excel_template(template_id: int, data: ExcelTemplateApply, db: Session = Depends(get_db)):
    """应用指定Excel模板批量生成申报文档"""
    # 校验Excel模板
    excel_template = db.query(ExcelTemplate).filter(
        ExcelTemplate.id == template_id,
        ExcelTemplate.status == "active"
    ).first()
    if not excel_template:
        raise HTTPException(status_code=404, detail="Excel模板不存在或已禁用")

    # 校验Word模板
    word_template = db.query(Template).filter(
        Template.id == data.word_template_id,
        Template.status == "active"
    ).first()
    if not word_template:
        raise HTTPException(status_code=404, detail="Word模板不存在或已禁用")

    # 批量生成文档
    output_dir = os.path.join(UPLOAD_DIR, "base_documents")
    try:
        results = ExcelHandler.batch_generate_documents(
            word_template_path=word_template.file_path,
            excel_path=excel_template.file_path,
            output_dir=output_dir
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量生成文档失败: {str(e)}")

    # 为成功生成的文档创建数据库记录
    for result in results:
        if result["status"] == "success":
            base_document = BaseDocument(
                template_id=data.word_template_id,
                base_code=result["base_code"],
                base_name=result["base_name"],
                version=1,
                file_path=result["file_path"]
            )
            db.add(base_document)
    db.commit()

    return {
        "total": len(results),
        "success": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] != "success"]),
        "details": results
    }
