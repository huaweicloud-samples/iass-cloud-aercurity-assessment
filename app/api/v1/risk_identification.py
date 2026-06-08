"""申报风险识别API"""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import User, Base_, RiskIdentification
from app.core.auth import get_current_user, RoleChecker

allow_eval_admin = RoleChecker("eval_admin")

router = APIRouter(prefix="/api/v1/risk", tags=["申报风险识别"])


# ============ Schemas ============

class RiskIdentificationCreate(BaseModel):
    base_id: str = Field(..., description="基地ID")
    # 1) 局点信息
    site_name: Optional[str] = None
    site_ip: Optional[str] = None
    region_name: Optional[str] = None
    # 2) 服务器规模及安可计划
    xinchuang_servers: Optional[int] = None
    x86_servers: Optional[int] = None
    # 3) 测评通过情况
    dengbao_passed: Optional[str] = None
    mipin_passed: Optional[str] = None
    # 4) 运营运维模式
    asset_huawei: Optional[str] = None
    contract_direct: Optional[str] = None
    # 5) 物理机房
    exclusive_room: Optional[str] = None
    l1_huawei_supplier: Optional[str] = None
    access_compliant: Optional[str] = None
    # 状态
    is_completed: bool = False
    current_step: int = 1


class RiskIdentificationResponse(BaseModel):
    id: str
    base_id: str
    user_id: str
    site_name: Optional[str] = None
    site_ip: Optional[str] = None
    region_name: Optional[str] = None
    xinchuang_servers: Optional[int] = None
    x86_servers: Optional[int] = None
    dengbao_passed: Optional[str] = None
    mipin_passed: Optional[str] = None
    asset_huawei: Optional[str] = None
    contract_direct: Optional[str] = None
    exclusive_room: Optional[str] = None
    l1_huawei_supplier: Optional[str] = None
    access_compliant: Optional[str] = None
    is_completed: bool = False
    current_step: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RiskAssessmentResult(BaseModel):
    """风险评估结果"""
    id: str
    base_id: str
    base_name: Optional[str] = None
    user_id: str
    user_name: Optional[str] = None
    is_completed: bool
    current_step: int
    # 局点信息
    site_name: Optional[str] = None
    site_ip: Optional[str] = None
    region_name: Optional[str] = None
    # 服务器规模
    xinchuang_servers: Optional[int] = None
    x86_servers: Optional[int] = None
    total_servers: Optional[int] = None
    xinchuang_ratio: Optional[float] = None
    server_check: Optional[str] = None  # pass/fail
    xinchuang_check: Optional[str] = None  # pass/fail
    # 测评
    dengbao_passed: Optional[str] = None
    mipin_passed: Optional[str] = None
    # 运营运维
    asset_huawei: Optional[str] = None
    contract_direct: Optional[str] = None
    # 物理机房
    exclusive_room: Optional[str] = None
    l1_huawei_supplier: Optional[str] = None
    access_compliant: Optional[str] = None
    # 综合评估
    overall_risk: Optional[str] = None  # high/medium/low
    risk_items: list = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============ API ============

@router.get("/check/{base_id}", summary="检查基地是否已填写风险识别")
async def check_risk_identification(
    base_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """检查指定基地是否已有风险识别记录"""
    record = db.query(RiskIdentification).filter(
        RiskIdentification.base_id == base_id,
        RiskIdentification.user_id == current_user.id,
    ).first()
    if record:
        return {"exists": True, "is_completed": record.is_completed, "current_step": record.current_step, "id": record.id}
    return {"exists": False, "is_completed": False, "current_step": 1, "id": None}


@router.get("/my", summary="获取当前用户的风险识别记录")
async def get_my_risk_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户所有基地的风险识别记录"""
    records = db.query(RiskIdentification).filter(
        RiskIdentification.user_id == current_user.id,
    ).all()
    return {"records": [_to_response(r, db) for r in records]}


@router.get("/base/{base_id}", summary="获取基地的风险识别记录")
async def get_base_risk_record(
    base_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定基地当前用户的风险识别记录"""
    record = db.query(RiskIdentification).filter(
        RiskIdentification.base_id == base_id,
        RiskIdentification.user_id == current_user.id,
    ).first()
    if not record:
        return {"record": None}
    return {"record": _to_response(record, db)}


@router.post("", summary="创建/更新风险识别记录")
async def save_risk_identification(
    data: RiskIdentificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """保存风险识别信息（创建或更新）"""
    # 查找已有记录
    record = db.query(RiskIdentification).filter(
        RiskIdentification.base_id == data.base_id,
        RiskIdentification.user_id == current_user.id,
    ).first()

    if record:
        # 更新
        for key, value in data.model_dump(exclude={"base_id"}).items():
            setattr(record, key, value)
        record.updated_at = datetime.now()
        db.commit()
        db.refresh(record)
    else:
        # 创建
        record = RiskIdentification(
            base_id=data.base_id,
            user_id=current_user.id,
            **data.model_dump(exclude={"base_id"}),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    return _to_response(record, db)


@router.get("/all", summary="获取所有风险识别记录(管理员)")
async def get_all_risk_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin),
):
    """管理员获取所有风险识别记录"""
    records = db.query(RiskIdentification).all()
    return {"records": [_to_response(r, db) for r in records]}


@router.delete("/{record_id}", summary="删除风险识别记录")
async def delete_risk_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_eval_admin),
):
    record = db.query(RiskIdentification).filter(RiskIdentification.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "删除成功"}


def _to_response(record: RiskIdentification, db: Session) -> dict:
    """将RiskIdentification转为带评估结果的响应"""
    base = db.query(Base_).filter(Base_.id == record.base_id).first()
    user = db.query(User).filter(User.id == record.user_id).first()

    # 计算服务器规模评估
    total_servers = None
    xinchuang_ratio = None
    server_check = None
    xinchuang_check = None
    risk_items = []

    if record.xinchuang_servers is not None and record.x86_servers is not None:
        total_servers = record.xinchuang_servers + record.x86_servers
        if total_servers > 0:
            xinchuang_ratio = round(record.xinchuang_servers / total_servers * 100, 1)
        # 评估要求：物理服务器不低于100台
        if total_servers >= 100:
            server_check = "pass"
        else:
            server_check = "fail"
            risk_items.append(f"物理服务器总数{total_servers}台，不满足不低于100台要求")
        # 信创服务器占比不低于60%
        if xinchuang_ratio is not None and xinchuang_ratio >= 60:
            xinchuang_check = "pass"
        else:
            xinchuang_check = "fail"
            risk_items.append(f"信创服务器占比{xinchuang_ratio}%，不满足不低于60%要求")

    # 综合风险评估
    overall_risk = "low"
    if risk_items:
        overall_risk = "high"
    if record.dengbao_passed == "no":
        risk_items.append("等保测评未通过或不在有效期")
        overall_risk = "high"
    if record.mipin_passed == "no":
        risk_items.append("密评未通过")
        overall_risk = "high"
    if not record.is_completed:
        overall_risk = "medium"

    return {
        "id": record.id,
        "base_id": record.base_id,
        "base_name": base.name if base else None,
        "user_id": record.user_id,
        "user_name": user.username if user else None,
        "is_completed": record.is_completed,
        "current_step": record.current_step,
        "site_name": record.site_name,
        "site_ip": record.site_ip,
        "region_name": record.region_name,
        "xinchuang_servers": record.xinchuang_servers,
        "x86_servers": record.x86_servers,
        "total_servers": total_servers,
        "xinchuang_ratio": xinchuang_ratio,
        "server_check": server_check,
        "xinchuang_check": xinchuang_check,
        "dengbao_passed": record.dengbao_passed,
        "mipin_passed": record.mipin_passed,
        "asset_huawei": record.asset_huawei,
        "contract_direct": record.contract_direct,
        "exclusive_room": record.exclusive_room,
        "l1_huawei_supplier": record.l1_huawei_supplier,
        "access_compliant": record.access_compliant,
        "overall_risk": overall_risk,
        "risk_items": risk_items,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }
