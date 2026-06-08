"""标杆管理API + 交互引导API + 基地管理API + LLM配置API"""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import (
    Benchmark, BenchmarkMaterial, Base_, Item, LLMConfig, User
)
from app.schemas.audit import (
    BenchmarkCreate, BenchmarkResponse, BenchmarkMaterialResponse,
    BaseCreate, BaseResponse, LLMConfigCreate, LLMConfigResponse,
    GuideRequest, GuideResponse
)
from app.core.auth import get_current_user, RoleChecker, require_base_access
from app.agents.audit_workflow import AuditWorkflow, rag_service, vector_store
from app.services.llm_service import LLMService
from config import UPLOAD_DIR, MAX_FILE_SIZE

# ============ 标杆管理 ============
router_benchmark = APIRouter(prefix="/api/v1/benchmarks", tags=["标杆管理"])
allow_eval_admin = RoleChecker("eval_admin")


@router_benchmark.post("", response_model=BenchmarkResponse, summary="创建标杆基地")
async def create_benchmark(
    data: BenchmarkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin)
):
    benchmark = Benchmark(name=data.name, description=data.description)
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)
    return benchmark


@router_benchmark.get("", summary="获取标杆基地列表")
async def get_benchmarks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    benchmarks = db.query(Benchmark).filter(Benchmark.status == "active").all()
    return {"total": len(benchmarks), "benchmarks": [BenchmarkResponse.model_validate(b) for b in benchmarks]}


@router_benchmark.post("/{benchmark_id}/materials/upload", summary="上传标杆材料")
async def upload_benchmark_material(
    benchmark_id: str,
    item_id: str = Form(...),
    material_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin)
):
    benchmark = db.query(Benchmark).filter(Benchmark.id == benchmark_id).first()
    if not benchmark:
        raise HTTPException(status_code=404, detail="标杆基地不存在")

    content = await file.read()
    file_dir = os.path.join(UPLOAD_DIR, "benchmark_materials", benchmark_id, item_id)
    os.makedirs(file_dir, exist_ok=True)
    file_path = os.path.join(file_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(content)

    # 提取文本
    content_text = ""
    try:
        from app.services.ocr_service import ocr_service
        content_text = ocr_service.recognize(file_path)
    except:
        pass

    # 向量嵌入
    embedding_id = None
    try:
        llm = LLMService()
        embedding = llm.get_embedding(content_text[:2000])
        embedding_id = rag_service.insert_embedding(embedding, {
            "item_id": item_id,
            "benchmark_id": benchmark_id,
            "material_type": material_type,
            "content_text": content_text[:2000]
        })
    except:
        pass

    material = BenchmarkMaterial(
        item_id=item_id,
        benchmark_id=benchmark_id,
        material_type=material_type,
        file_path=file_path,
        content_text=content_text,
        embedding_id=embedding_id
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return BenchmarkMaterialResponse.model_validate(material)


# ============ 基地管理 ============
router_base = APIRouter(prefix="/api/v1/bases", tags=["基地管理"])


@router_base.post("", response_model=BaseResponse, summary="创建基地")
async def create_base(
    data: BaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin)
):
    base = Base_(name=data.name, code=data.code)
    db.add(base)
    db.commit()
    db.refresh(base)
    return base


@router_base.get("", summary="获取基地列表")
async def get_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bases = db.query(Base_).all()
    return {"total": len(bases), "bases": [BaseResponse.model_validate(b) for b in bases]}


@router_base.get("/{base_id}", response_model=BaseResponse, summary="获取基地详情")
async def get_base(
    base_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    base = db.query(Base_).filter(Base_.id == base_id).first()
    if not base:
        raise HTTPException(status_code=404, detail="基地不存在")
    return base


# ============ 交互引导 ============
router_guide = APIRouter(prefix="/api/v1/guide", tags=["交互引导"])


@router_guide.post("", summary="交互式智能引导")
async def interactive_guide(
    data: GuideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_base_access(data.base_id, current_user)

    item = db.query(Item).filter(Item.id == data.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")

    try:
        workflow = AuditWorkflow()
        result = workflow.run_guide(
            item_id=data.item_id,
            item_requirement=item.requirement,
            base_id=data.base_id,
            user_input=data.user_input or ""
        )
        return {
            "questions": result.get("guide_questions", []),
            "standard_interpretation": result.get("standard_interpretation", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"引导生成失败: {e}")


# ============ LLM配置 ============
router_llm = APIRouter(prefix="/api/v1/llm-configs", tags=["大模型配置"])


@router_llm.post("", response_model=LLMConfigResponse, summary="配置大模型")
async def create_llm_config(
    data: LLMConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = LLMConfig(
        user_id=current_user.id,
        base_url=data.base_url,
        model_id=data.model_id,
        api_key=data.api_key,  # 生产环境应加密存储
        is_default=data.is_default
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router_llm.get("", summary="获取当前用户LLM配置")
async def get_llm_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    configs = db.query(LLMConfig).filter(LLMConfig.user_id == current_user.id).all()
    return {"configs": [LLMConfigResponse.model_validate(c) for c in configs]}
