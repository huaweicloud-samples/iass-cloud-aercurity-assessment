from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


# ============ 用户相关 ============

class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(default="base_user")
    assigned_bases: List[str] = Field(default_factory=list, description="关联基地ID列表，基地用户必填，管理员角色可为空")


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    assigned_bases: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============ 标准条目相关 ============

class ItemCreate(BaseModel):
    id: str = Field(..., max_length=20, description="条目ID,如5.1.1")
    requirement: str = Field(..., description="条目标准要求")
    section: str = Field(..., max_length=10, description="所属板块")
    item_type: Optional[str] = None


class ItemResponse(BaseModel):
    id: str
    requirement: str
    section: str
    item_type: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ItemListResponse(BaseModel):
    total: int
    items: List[ItemResponse]


# ============ 基地相关 ============

class BaseCreate(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)


class BaseResponse(BaseModel):
    id: str
    name: str
    code: str
    declaration_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ============ 材料相关 ============

class MaterialResponse(BaseModel):
    id: str
    item_id: str
    base_id: str
    material_type: str
    file_format: Optional[str]
    file_path: Optional[str]
    content_text: Optional[str]
    version: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class MaterialUpload(BaseModel):
    item_id: str
    base_id: str
    material_type: str = Field(..., description="description/evidence")
    content_text: Optional[str] = None


# ============ 审核记录相关 ============

class AuditRecordResponse(BaseModel):
    id: str
    item_id: str
    base_id: str
    result: str
    score: Optional[int]
    diagnosis: Optional[str]
    suggestion: Optional[str]
    auditor: str
    audited_at: datetime

    model_config = {"from_attributes": True}


class AuditRequest(BaseModel):
    item_id: str
    base_id: str


# ============ 标杆相关 ============

class BenchmarkCreate(BaseModel):
    name: str
    description: Optional[str] = None


class BenchmarkResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BenchmarkMaterialResponse(BaseModel):
    id: str
    item_id: str
    benchmark_id: str
    material_type: str
    file_path: Optional[str]
    content_text: Optional[str]

    model_config = {"from_attributes": True}


# ============ LLM配置相关 ============

class LLMConfigCreate(BaseModel):
    base_url: str
    model_id: str
    api_key: str
    is_default: bool = False


class LLMConfigResponse(BaseModel):
    id: int
    user_id: str
    base_url: str
    model_id: str
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ============ 交互引导相关 ============

class GuideRequest(BaseModel):
    item_id: str
    base_id: str
    user_input: Optional[str] = None


class GuideResponse(BaseModel):
    questions: List[str]
    draft_content: Optional[str]
    evidence_checklist: List[str]


# ============ 统一API响应 ============

class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict | list] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
