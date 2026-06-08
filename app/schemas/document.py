from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


# ============ 模板相关 ============

class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="模板名称")
    document_type: str = Field(..., min_length=1, max_length=100, description="文档类型")


class TemplateResponse(BaseModel):
    id: int
    name: str
    document_type: str
    file_path: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TemplateListResponse(BaseModel):
    total: int
    templates: List[TemplateResponse]


# ============ 基地文档相关 ============

class BaseDocumentInit(BaseModel):
    template_id: int = Field(..., description="模板ID")
    base_code: str = Field(..., min_length=1, max_length=100, description="基地编码")
    base_name: str = Field(..., min_length=1, max_length=255, description="基地名称")


class BaseDocumentEdit(BaseModel):
    content_data: str = Field(..., description="编辑内容(JSON格式)")


class BaseDocumentResponse(BaseModel):
    id: int
    template_id: int
    base_code: str
    base_name: str
    version: int
    file_path: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BaseDocumentListResponse(BaseModel):
    total: int
    documents: List[BaseDocumentResponse]


# ============ 文档内容相关 ============

class DocumentContentResponse(BaseModel):
    id: int
    document_id: int
    content_type: str
    content_data: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ============ Excel模板相关 ============

class ExcelTemplateResponse(BaseModel):
    id: int
    name: str
    file_path: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExcelTemplateListResponse(BaseModel):
    total: int
    templates: List[ExcelTemplateResponse]


class ExcelTemplateApply(BaseModel):
    template_id: int = Field(..., description="Excel模板ID")
    word_template_id: int = Field(..., description="关联的Word模板ID")


# ============ 通用响应 ============

class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict | list] = None
