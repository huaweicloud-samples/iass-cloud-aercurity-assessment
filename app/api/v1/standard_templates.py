"""标准项刷新模板管理API - 支持模板一键上传与自动解析"""
import os
import uuid
import json
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Template, BaseDocument, DocumentContent
from app.schemas.document import TemplateResponse
from app.utils.document_handler import DocumentHandler, ExcelHandler
from config import TEMPLATE_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

router = APIRouter(prefix="/api/v1/standard-templates", tags=["标准项刷新"])


class ContentItem(BaseModel):
    content_type: str
    content_data: str


class SaveEditRequest(BaseModel):
    template_id: int
    base_id: str
    base_name: str
    contents: List[ContentItem]


@router.post("/upload", summary="一键上传标准项模板")
async def upload_standard_template(
    file: UploadFile = File(...),
    name: str = Form(None),
    db: Session = Depends(get_db)
):
    """管理员一键上传标准项模板，系统自动识别并解析模板内容"""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式，仅允许: {', '.join(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制({MAX_FILE_SIZE // 1024 // 1024}MB)")

    # 保存文件
    standard_dir = os.path.join(TEMPLATE_DIR, "standard")
    os.makedirs(standard_dir, exist_ok=True)

    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(standard_dir, unique_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # 自动解析模板内容
    parsed_content = []
    template_info = {}
    try:
        if ext in (".docx",):
            parsed_content = DocumentHandler.parse_word_document(file_path)
            template_info = DocumentHandler.get_document_info(file_path)
        elif ext in (".xlsx", ".xls"):
            excel_data = ExcelHandler.parse_excel_template(file_path)
            template_info = {
                "sheets": list(excel_data.keys()),
                "sheet_details": {
                    k: {"columns": v["columns"], "row_count": v["row_count"]}
                    for k, v in excel_data.items()
                }
            }
            # 将Excel数据转为统一格式
            for sheet_name, sheet_data in excel_data.items():
                parsed_content.append({
                    "content_type": "table",
                    "content_data": json.dumps({
                        "sheet_name": sheet_name,
                        "rows": sheet_data["row_count"],
                        "cols": len(sheet_data["columns"]),
                        "columns": sheet_data["columns"],
                        "data": sheet_data["data"]
                    }, ensure_ascii=False)
                })
    except Exception as e:
        parsed_content = []
        template_info = {"error": str(e)}

    # 创建数据库记录
    template_name = name or file.filename
    template = Template(
        name=template_name,
        document_type="标准项",
        file_path=file_path,
        status="active"
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    return {
        "template": TemplateResponse.model_validate(template),
        "parsed_content": parsed_content,
        "template_info": template_info,
    }


@router.get("", summary="获取标准项模板列表及内容")
async def get_standard_templates(db: Session = Depends(get_db)):
    """获取所有标准项模板及其解析内容"""
    templates = db.query(Template).filter(
        Template.document_type == "标准项",
        Template.status == "active"
    ).order_by(Template.created_at.desc()).all()

    result = []
    for t in templates:
        parsed_content = []
        template_info = {}
        try:
            if os.path.exists(t.file_path):
                ext = os.path.splitext(t.file_path)[1].lower()
                if ext in (".docx",):
                    parsed_content = DocumentHandler.parse_word_document(t.file_path)
                    template_info = DocumentHandler.get_document_info(t.file_path)
                elif ext in (".xlsx", ".xls"):
                    excel_data = ExcelHandler.parse_excel_template(t.file_path)
                    template_info = {
                        "sheets": list(excel_data.keys()),
                        "sheet_details": {
                            k: {"columns": v["columns"], "row_count": v["row_count"]}
                            for k, v in excel_data.items()
                        }
                    }
                    for sheet_name, sheet_data in excel_data.items():
                        parsed_content.append({
                            "content_type": "table",
                            "content_data": json.dumps({
                                "sheet_name": sheet_name,
                                "rows": sheet_data["row_count"],
                                "cols": len(sheet_data["columns"]),
                                "columns": sheet_data["columns"],
                                "data": sheet_data["data"]
                            }, ensure_ascii=False)
                        })
        except Exception as e:
            print(f"解析模板失败 {t.file_path}: {e}")
            import traceback
            traceback.print_exc()
        result.append({
            "template": TemplateResponse.model_validate(t),
            "parsed_content": parsed_content,
            "template_info": template_info,
        })

    return {"total": len(result), "templates": result}


@router.delete("/{template_id}", summary="删除指定标准项模板")
async def delete_standard_template(template_id: int, db: Session = Depends(get_db)):
    """删除指定标准项模板"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if template.file_path and os.path.exists(template.file_path):
        os.remove(template.file_path)

    db.delete(template)
    db.commit()
    return {"code": 200, "message": "删除成功"}


# ============ 基地用户编辑保存接口 ============

@router.post("/save", summary="基地用户保存编辑内容")
async def save_base_edit(
    data: SaveEditRequest,
    db: Session = Depends(get_db)
):
    """基地用户按照管理员上传的标准项模板进行编辑，按基地维度保存"""
    template = db.query(Template).filter(
        Template.id == data.template_id,
        Template.status == "active"
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或已禁用")

    base_doc = db.query(BaseDocument).filter(
        BaseDocument.template_id == data.template_id,
        BaseDocument.base_code == data.base_id
    ).first()

    if base_doc:
        db.query(DocumentContent).filter(DocumentContent.document_id == base_doc.id).delete()
        base_doc.base_name = data.base_name
        base_doc.version += 1
        base_doc.updated_at = datetime.now()
    else:
        base_doc = BaseDocument(
            template_id=data.template_id,
            base_code=data.base_id,
            base_name=data.base_name,
            version=1,
            file_path=template.file_path
        )
        db.add(base_doc)
        db.flush()

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


@router.get("/edit/{template_id}/{base_id}", summary="获取基地用户编辑内容")
async def get_base_edit(
    template_id: int,
    base_id: str,
    db: Session = Depends(get_db)
):
    """获取指定模板+基地的编辑内容，若无则返回模板原始内容"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    base_doc = db.query(BaseDocument).filter(
        BaseDocument.template_id == template_id,
        BaseDocument.base_code == base_id
    ).first()

    if base_doc:
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
            ext = os.path.splitext(template.file_path)[1].lower()
            if ext in (".docx",):
                parsed_content = DocumentHandler.parse_word_document(template.file_path)
            elif ext in (".xlsx", ".xls"):
                excel_data = ExcelHandler.parse_excel_template(template.file_path)
                for sheet_name, sheet_data in excel_data.items():
                    parsed_content.append({
                        "content_type": "table",
                        "content_data": json.dumps({
                            "sheet_name": sheet_name,
                            "rows": sheet_data["row_count"],
                            "cols": len(sheet_data["columns"]),
                            "columns": sheet_data["columns"],
                            "data": sheet_data["data"]
                        }, ensure_ascii=False)
                    })
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


@router.get("/edits/{base_id}", summary="获取基地所有标准项编辑记录")
async def get_base_all_edits(
    base_id: str,
    db: Session = Depends(get_db)
):
    """获取指定基地在标准项下所有模板的编辑状态"""
    templates = db.query(Template).filter(
        Template.document_type == "标准项",
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

    return {"base_id": base_id, "edits": result}
