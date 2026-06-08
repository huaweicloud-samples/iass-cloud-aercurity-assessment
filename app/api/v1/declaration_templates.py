"""申报书刷新模板管理API - 支持01-06子目录模板上传与自动解析"""
import os
import uuid
import json
from datetime import datetime
from typing import Optional, List
from fastapi.responses import FileResponse

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Template, BaseDocument, DocumentContent
from app.schemas.document import TemplateResponse, TemplateListResponse
from app.utils.document_handler import DocumentHandler
from config import TEMPLATE_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

router = APIRouter(prefix="/api/v1/declaration-templates", tags=["申报书刷新"])

# 合法的子目录
VALID_CATEGORIES = ["01", "02", "03", "04", "05", "06"]


class ContentItem(BaseModel):
    content_type: str
    content_data: str


class SaveEditRequest(BaseModel):
    template_id: int
    base_id: str
    base_name: str
    contents: List[ContentItem]


@router.post("/{category}/upload", summary="一键上传模板到指定目录")
async def upload_category_template(
    category: str,
    file: UploadFile = File(...),
    name: str = Form(None),
    db: Session = Depends(get_db)
):
    """管理员一键上传模板到01-06子目录，系统自动识别并解析模板内容"""
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"无效的目录编号，仅支持: {', '.join(VALID_CATEGORIES)}")

    # 校验文件扩展名
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式，仅允许: {', '.join(ALLOWED_EXTENSIONS)}")

    # 校验文件大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制({MAX_FILE_SIZE // 1024 // 1024}MB)")

    # 保存到对应子目录
    category_dir = os.path.join(TEMPLATE_DIR, category)
    os.makedirs(category_dir, exist_ok=True)

    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(category_dir, unique_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # 自动解析模板内容
    parsed_content = []
    template_info = {}
    try:
        parsed_content = DocumentHandler.parse_word_document(file_path)
        template_info = DocumentHandler.get_document_info(file_path)
    except Exception as e:
        parsed_content = []
        template_info = {"error": str(e)}

    # 创建数据库记录
    template_name = name or file.filename
    template = Template(
        name=template_name,
        document_type=f"申报书-{category}",
        file_path=file_path,
        status="active"
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    return {
        "template": TemplateResponse.model_validate(template),
        "category": category,
        "parsed_content": parsed_content,
        "template_info": template_info,
    }


@router.get("/{category}", summary="获取指定目录的模板列表及内容")
async def get_category_templates(
    category: str,
    db: Session = Depends(get_db)
):
    """获取指定目录(01-06)下的所有模板及其解析内容"""
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"无效的目录编号，仅支持: {', '.join(VALID_CATEGORIES)}")

    templates = db.query(Template).filter(
        Template.document_type == f"申报书-{category}",
        Template.status == "active"
    ).order_by(Template.created_at.desc()).all()

    # 为每个模板解析内容
    result = []
    for t in templates:
        parsed_content = []
        template_info = {}
        try:
            if os.path.exists(t.file_path):
                parsed_content = DocumentHandler.parse_word_document(t.file_path)
                template_info = DocumentHandler.get_document_info(t.file_path)
        except:
            pass
        result.append({
            "template": TemplateResponse.model_validate(t),
            "parsed_content": parsed_content,
            "template_info": template_info,
        })

    return {"category": category, "total": len(result), "templates": result}


@router.get("", summary="获取所有目录的模板概览")
async def get_all_category_overview(db: Session = Depends(get_db)):
    """获取01-06所有目录的模板概览"""
    overview = []
    for category in VALID_CATEGORIES:
        count = db.query(Template).filter(
            Template.document_type == f"申报书-{category}",
            Template.status == "active"
        ).count()
        overview.append({"category": category, "template_count": count})
    return {"categories": overview}


@router.delete("/{template_id}", summary="删除指定模板")
async def delete_category_template(template_id: int, db: Session = Depends(get_db)):
    """删除指定模板"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 删除文件
    if template.file_path and os.path.exists(template.file_path):
        os.remove(template.file_path)

    db.delete(template)
    db.commit()
    return {"code": 200, "message": "删除成功"}


# ============ 基地用户编辑保存接口 ============

@router.post("/{category}/save", summary="基地用户保存编辑内容")
async def save_base_edit(
    category: str,
    data: SaveEditRequest,
    db: Session = Depends(get_db)
):
    """基地用户按照管理员上传的模板进行编辑，按基地维度保存"""
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"无效的目录编号")

    # 校验模板存在
    template = db.query(Template).filter(
        Template.id == data.template_id,
        Template.status == "active"
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或已禁用")

    # 查找或创建基地文档记录
    base_doc = db.query(BaseDocument).filter(
        BaseDocument.template_id == data.template_id,
        BaseDocument.base_code == data.base_id
    ).first()

    if base_doc:
        # 更新已有记录：先删除旧内容
        db.query(DocumentContent).filter(DocumentContent.document_id == base_doc.id).delete()
        base_doc.base_name = data.base_name
        base_doc.version += 1
        base_doc.updated_at = datetime.now()
    else:
        # 创建新记录
        base_doc = BaseDocument(
            template_id=data.template_id,
            base_code=data.base_id,
            base_name=data.base_name,
            version=1,
            file_path=template.file_path
        )
        db.add(base_doc)
        db.flush()

    # 保存编辑内容
    for item in data.contents:
        content = DocumentContent(
            document_id=base_doc.id,
            content_type=item.content_type,
            content_data=item.content_data
        )
        db.add(content)

    db.commit()
    db.refresh(base_doc)

    return {
        "code": 200,
        "message": "保存成功",
        "document_id": base_doc.id,
        "version": base_doc.version,
    }


@router.get("/{category}/edit/{template_id}/{base_id}", summary="获取基地用户编辑内容")
async def get_base_edit(
    category: str,
    template_id: int,
    base_id: str,
    db: Session = Depends(get_db)
):
    """获取指定模板+基地的编辑内容，若无则返回模板原始内容"""
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"无效的目录编号")

    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 查找基地编辑内容
    base_doc = db.query(BaseDocument).filter(
        BaseDocument.template_id == template_id,
        BaseDocument.base_code == base_id
    ).first()

    if base_doc:
        # 返回基地已编辑内容
        contents = db.query(DocumentContent).filter(
            DocumentContent.document_id == base_doc.id
        ).all()
        return {
            "template_id": template_id,
            "base_id": base_id,
            "base_name": base_doc.base_name,
            "version": base_doc.version,
            "is_edited": True,
            "contents": [
                {"content_type": c.content_type, "content_data": c.content_data}
                for c in contents
            ],
            "updated_at": base_doc.updated_at.isoformat() if base_doc.updated_at else None,
        }

    # 返回模板原始内容
    parsed_content = []
    try:
        if os.path.exists(template.file_path):
            parsed_content = DocumentHandler.parse_word_document(template.file_path)
    except:
        pass

    return {
        "template_id": template_id,
        "base_id": base_id,
        "base_name": "",
        "version": 0,
        "is_edited": False,
        "contents": parsed_content,
        "updated_at": None,
    }


@router.get("/{category}/edits/{base_id}", summary="获取基地在指定目录下所有编辑记录")
async def get_base_all_edits(
    category: str,
    base_id: str,
    db: Session = Depends(get_db)
):
    """获取指定基地在某个目录下所有模板的编辑状态"""
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"无效的目录编号")

    templates = db.query(Template).filter(
        Template.document_type == f"申报书-{category}",
        Template.status == "active"
    ).all()

    result = []
    for t in templates:
        base_doc = db.query(BaseDocument).filter(
            BaseDocument.template_id == t.id,
            BaseDocument.base_code == base_id
        ).first()
        result.append({
            "template_id": t.id,
            "template_name": t.name,
            "is_edited": base_doc is not None,
            "version": base_doc.version if base_doc else 0,
            "updated_at": base_doc.updated_at.isoformat() if base_doc and base_doc.updated_at else None,
        })

    return {"category": category, "base_id": base_id, "edits": result}


@router.get("/{category}/download/{template_id}/{base_id}", summary="下载基地编辑后的文档")
async def download_base_document(
    category: str,
    template_id: int,
    base_id: str,
    db: Session = Depends(get_db)
):
    """下载指定基地编辑后的Word文档，保持模板格式"""
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"无效的目录编号")

    # 校验模板存在
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.document_type == f"申报书-{category}",
        Template.status == "active"
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或已禁用")

    # 查找基地编辑内容
    base_doc = db.query(BaseDocument).filter(
        BaseDocument.template_id == template_id,
        BaseDocument.base_code == base_id
    ).first()

    if not base_doc:
        raise HTTPException(status_code=404, detail="该基地尚未编辑此文档")

    # 获取编辑内容
    contents = db.query(DocumentContent).filter(
        DocumentContent.document_id == base_doc.id
    ).order_by(DocumentContent.id).all()

    if not contents:
        raise HTTPException(status_code=404, detail="未找到编辑内容")

    # 转换为列表格式
    contents_list = [
        {
            "content_type": c.content_type,
            "content_data": c.content_data
        }
        for c in contents
    ]

    # 生成临时文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_filename = f"{base_doc.base_name}_{category}_{timestamp}.docx"
    temp_path = os.path.join(TEMPLATE_DIR, category, temp_filename)

    try:
        # 根据编辑内容生成Word文档
        DocumentHandler.generate_word_document_from_contents(
            template_path=template.file_path,
            contents=contents_list,
            output_path=temp_path
        )

        # 返回文件
        return FileResponse(
            path=temp_path,
            filename=f"{base_doc.base_name}_{category}_v{base_doc.version}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"生成文档失败: {str(e)}")
