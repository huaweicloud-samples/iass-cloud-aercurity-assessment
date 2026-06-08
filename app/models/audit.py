import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="base_user")  # sys_admin/eval_admin/base_user/auditor
    assigned_bases = Column(Text, default="[]")  # JSON数组，基地ID列表
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    llm_configs = relationship("LLMConfig", back_populates="user")


class Item(Base):
    """标准条目表"""
    __tablename__ = "items"

    id = Column(String(20), primary_key=True)  # 如"5.1.1"
    requirement = Column(Text, nullable=False, comment="条目标准要求")
    section = Column(String(10), nullable=False, index=True, comment="所属板块")
    item_type = Column(String(20), comment="条目类型")
    status = Column(String(20), default="pending", index=True, comment="审核状态")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    materials = relationship("Material", back_populates="item")
    audit_records = relationship("AuditRecord", back_populates="item")
    benchmark_materials = relationship("BenchmarkMaterial", back_populates="item")


class Base_(Base):
    """基地表"""
    __tablename__ = "bases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    declaration_status = Column(String(20), default="pending")
    admin_users = Column(Text, default="[]")  # JSON数组
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    materials = relationship("Material", back_populates="base")
    audit_records = relationship("AuditRecord", back_populates="base")


class Material(Base):
    """申报材料表"""
    __tablename__ = "materials"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    item_id = Column(String(20), ForeignKey("items.id"), nullable=False, index=True)
    base_id = Column(String(36), ForeignKey("bases.id"), nullable=False, index=True)
    material_type = Column(String(20), nullable=False)  # description/evidence
    file_format = Column(String(10))
    file_path = Column(String(500))
    content_text = Column(Text, comment="AI提取文本内容")
    version = Column(Integer, default=1)
    uploaded_at = Column(DateTime, default=datetime.now)

    item = relationship("Item", back_populates="materials")
    base = relationship("Base_", back_populates="materials")


class AuditRecord(Base):
    """审核记录表"""
    __tablename__ = "audit_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    item_id = Column(String(20), ForeignKey("items.id"), nullable=False)
    base_id = Column(String(36), ForeignKey("bases.id"), nullable=False)
    result = Column(String(20), nullable=False)  # pass/fail/pending
    score = Column(Integer, comment="合规得分")
    diagnosis = Column(Text, comment="AI诊断结论")
    suggestion = Column(Text, comment="整改建议")
    auditor = Column(String(50), default="AI")
    audited_at = Column(DateTime, default=datetime.now)

    item = relationship("Item", back_populates="audit_records")
    base = relationship("Base_", back_populates="audit_records")


class Benchmark(Base):
    """标杆基地表"""
    __tablename__ = "benchmarks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.now)

    materials = relationship("BenchmarkMaterial", back_populates="benchmark")


class BenchmarkMaterial(Base):
    """标杆材料表"""
    __tablename__ = "benchmark_materials"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    item_id = Column(String(20), ForeignKey("items.id"), nullable=False)
    benchmark_id = Column(String(36), ForeignKey("benchmarks.id"), nullable=False)
    material_type = Column(String(20), nullable=False)
    file_path = Column(String(500))
    content_text = Column(Text)
    embedding_id = Column(String(100), comment="Milvus中的向量ID")

    item = relationship("Item", back_populates="benchmark_materials")
    benchmark = relationship("Benchmark", back_populates="materials")


class LLMConfig(Base):
    """大模型配置表"""
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    base_url = Column(String(500), nullable=False)
    model_id = Column(String(100), nullable=False)
    api_key = Column(String(500), nullable=False, comment="加密存储")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="llm_configs")


class RiskIdentification(Base):
    """申报风险识别表"""
    __tablename__ = "risk_identifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    base_id = Column(String(36), ForeignKey("bases.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    # 1) 局点信息
    site_name = Column(String(200), comment="局点名称")
    site_ip = Column(String(100), comment="IP地址")
    region_name = Column(String(200), comment="Region名称")
    # 2) 服务器规模及安可计划
    xinchuang_servers = Column(Integer, comment="信创服务器数量（台）")
    x86_servers = Column(Integer, comment="X86服务器数量（台）")
    # 3) 测评通过情况
    dengbao_passed = Column(String(10), comment="等保测评是否通过并在有效期(yes/no)")
    mipin_passed = Column(String(10), comment="密评通过情况(yes/no)")
    # 4) 运营运维模式
    asset_huawei = Column(String(10), comment="资产归属华为(yes/no)")
    contract_direct = Column(String(10), comment="合同是否与政府客户直签(yes/no)")
    # 5) 物理机房
    exclusive_room = Column(String(10), comment="是否独享机房(yes/no)")
    l1_huawei_supplier = Column(String(10), comment="L1是否是华为供应商(yes/no)")
    access_compliant = Column(String(10), comment="人员进出机房是否符合华为数据中心要求(yes/no)")
    # 状态
    is_completed = Column(Boolean, default=False, comment="是否已完成填写")
    current_step = Column(Integer, default=1, comment="当前填写步骤(1-5)")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
