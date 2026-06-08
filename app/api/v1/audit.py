"""智能审核API - Agent工作流触发与结果查询"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import Item, Base_, Material, AuditRecord, User
from app.schemas.audit import AuditRequest, AuditRecordResponse
from app.core.auth import get_current_user, RoleChecker, require_base_access
from app.agents.audit_workflow import AuditWorkflow
from app.services.llm_service import LLMService

router = APIRouter(prefix="/api/v1/audit", tags=["智能审核"])
allow_base_user = RoleChecker("base_user")


@router.post("/run", summary="执行智能审核")
async def run_audit(
    data: AuditRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_base_user)
):
    require_base_access(data.base_id, current_user)

    # 获取条目信息
    item = db.query(Item).filter(Item.id == data.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")

    # 获取申报材料
    materials = db.query(Material).filter(
        Material.item_id == data.item_id,
        Material.base_id == data.base_id
    ).all()
    submission_content = "\n".join(m.content_text or "" for m in materials)

    # 执行Agent审核工作流
    try:
        workflow = AuditWorkflow()
        result = workflow.run_full_audit(
            item_id=data.item_id,
            item_requirement=item.requirement,
            base_id=data.base_id,
            submission_content=submission_content
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"审核工作流执行失败: {e}")

    # 保存审核记录
    record = AuditRecord(
        item_id=data.item_id,
        base_id=data.base_id,
        result=result.get("audit_result", "fail"),
        score=result.get("score", 0),
        diagnosis=result.get("diagnosis", ""),
        suggestion=result.get("suggestion", ""),
        auditor="AI"
    )

    # 更新或插入
    existing = db.query(AuditRecord).filter(
        AuditRecord.item_id == data.item_id,
        AuditRecord.base_id == data.base_id
    ).first()
    if existing:
        existing.result = record.result
        existing.score = record.score
        existing.diagnosis = record.diagnosis
        existing.suggestion = record.suggestion
        existing.auditor = "AI"
    else:
        db.add(record)

    # 更新条目状态
    item.status = result.get("audit_result", "fail")
    db.commit()
    db.refresh(record if not existing else existing)

    return {
        "audit_result": result.get("audit_result"),
        "score": result.get("score", 0),
        "diagnosis": result.get("diagnosis", ""),
        "suggestion": result.get("suggestion", ""),
        "differences": result.get("differences", []),
        "standard_interpretation": result.get("standard_interpretation", ""),
    }


@router.get("/result/{item_id}/{base_id}", response_model=AuditRecordResponse, summary="获取审核结果")
async def get_audit_result(
    item_id: str,
    base_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_base_access(base_id, current_user)
    record = db.query(AuditRecord).filter(
        AuditRecord.item_id == item_id,
        AuditRecord.base_id == base_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="审核记录不存在")
    return record


@router.get("/results/{base_id}", summary="获取基地全部审核结果")
async def get_base_audit_results(
    base_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_base_access(base_id, current_user)
    records = db.query(AuditRecord).filter(AuditRecord.base_id == base_id).all()
    return {
        "total": len(records),
        "records": [AuditRecordResponse.model_validate(r) for r in records]
    }
