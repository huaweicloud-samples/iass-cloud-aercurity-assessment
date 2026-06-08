import os
import uuid
import json
import shutil
from datetime import datetime
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Template, BaseDocument, DocumentContent
from app.schemas.document import (
    BaseDocumentInit, BaseDocumentEdit, BaseDocumentResponse,
    BaseDocumentListResponse, DocumentContentResponse
)
from app.utils.document_handler import DocumentHandler
from config import UPLOAD_DIR

router = APIRouter(prefix="/api/documents/base", tags=["基地文档编辑"])


@router.post("/init-or-get", response_model=BaseDocumentResponse, summary="初始化基地文档或获取已有文档")
async def init_or_get_document(data: BaseDocumentInit, db: Session = Depends(get_db)):
    """用户选择模板，一键生成专属基地文档副本；若已存在则返回已有文档"""
    # 校验模板是否存在且有效
    template = db.query(Template).filter(
        Template.id == data.template_id,
        Template.status == "active"
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或已禁用")

    # 检查是否已存在该基地的该模板文档
    existing = db.query(BaseDocument).filter(
        BaseDocument.template_id == data.template_id,
        BaseDocument.base_code == data.base_code
    ).first()

    if existing:
        return existing

    # 基于模板创建新文档副本
    base_dir = os.path.join(UPLOAD_DIR, "base_documents", data.base_code)
    os.makedirs(base_dir, exist_ok=True)

    ext = os.path.splitext(template.file_path)[1]
    unique_filename = f"{data.base_code}_{template.name}_{uuid.uuid4().hex[:8]}{ext}"
    output_path = os.path.join(base_dir, unique_filename)

    DocumentHandler.create_document_from_template(template.file_path, output_path)

    # 解析文档内容并存储
    contents = DocumentHandler.parse_word_document(output_path)

    # 创建基地文档记录
    base_document = BaseDocument(
        template_id=data.template_id,
        base_code=data.base_code,
        base_name=data.base_name,
        version=1,
        file_path=output_path
    )
    db.add(base_document)
    db.commit()
    db.refresh(base_document)

    # 存储文档内容
    for content in contents:
        doc_content = DocumentContent(
            document_id=base_document.id,
            content_type=content["content_type"],
            content_data=content["content_data"]
        )
        db.add(doc_content)
    db.commit()

    return base_document


@router.get("/{base_code}", response_model=BaseDocumentListResponse, summary="获取基地所有文档列表")
async def get_base_documents(base_code: str, db: Session = Depends(get_db)):
    """根据基地代码获取该基地所有文档列表"""
    documents = db.query(BaseDocument).filter(
        BaseDocument.base_code == base_code
    ).order_by(BaseDocument.updated_at.desc()).all()
    return BaseDocumentListResponse(total=len(documents), documents=documents)


@router.get("/detail/{document_id}", summary="获取指定文档详细内容")
async def get_document_detail(document_id: int, db: Session = Depends(get_db)):
    """获取指定文档详细内容，包含文档信息和内容列表"""
    document = db.query(BaseDocument).filter(BaseDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    contents = db.query(DocumentContent).filter(
        DocumentContent.document_id == document_id
    ).all()

    return {
        "document": BaseDocumentResponse.model_validate(document),
        "contents": [DocumentContentResponse.model_validate(c) for c in contents]
    }


@router.put("/edit/{document_id}", response_model=BaseDocumentResponse, summary="在线编辑文档内容")
async def edit_document(document_id: int, data: BaseDocumentEdit, db: Session = Depends(get_db)):
    """在线编辑文档内容，自动生成新版本"""
    document = db.query(BaseDocument).filter(BaseDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 更新文档文件内容
    try:
        DocumentHandler.update_document_content(document.file_path, data.content_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档内容更新失败: {str(e)}")

    # 更新版本号
    document.version += 1
    document.updated_at = datetime.now()
    db.commit()
    db.refresh(document)

    # 更新文档内容记录
    contents = DocumentHandler.parse_word_document(document.file_path)
    # 删除旧内容
    db.query(DocumentContent).filter(DocumentContent.document_id == document_id).delete()
    # 写入新内容
    for content in contents:
        doc_content = DocumentContent(
            document_id=document.id,
            content_type=content["content_type"],
            content_data=content["content_data"]
        )
        db.add(doc_content)
    db.commit()

    return document


@router.post("/upload/{document_id}", response_model=BaseDocumentResponse, summary="上传本地编辑后的文档")
async def upload_edited_document(
    document_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传本地编辑后的文档，覆盖原文件并升级版本"""
    document = db.query(BaseDocument).filter(BaseDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    if not DocumentHandler.validate_file_extension(file.filename):
        raise HTTPException(status_code=400, detail="不支持的文件格式")

    content = await file.read()
    with open(document.file_path, "wb") as f:
        f.write(content)

    # 更新版本号
    document.version += 1
    document.updated_at = datetime.now()
    db.commit()
    db.refresh(document)

    # 重新解析文档内容
    contents = DocumentHandler.parse_word_document(document.file_path)
    db.query(DocumentContent).filter(DocumentContent.document_id == document_id).delete()
    for c in contents:
        doc_content = DocumentContent(
            document_id=document.id,
            content_type=c["content_type"],
            content_data=c["content_data"]
        )
        db.add(doc_content)
    db.commit()

    return document
