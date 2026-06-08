from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Template(Base):
    """文档模板表"""
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="模板名称")
    document_type = Column(String(100), nullable=False, comment="文档类型")
    file_path = Column(String(500), nullable=False, comment="模板文件存储路径")
    status = Column(String(20), default="active", comment="模板状态: active/inactive")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联关系
    base_documents = relationship("BaseDocument", back_populates="template")


class BaseDocument(Base):
    """基地文档表"""
    __tablename__ = "base_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False, comment="关联模板ID")
    base_code = Column(String(100), nullable=False, comment="基地唯一编码")
    base_name = Column(String(255), nullable=False, comment="基地名称")
    version = Column(Integer, default=1, comment="文档当前版本号")
    file_path = Column(String(500), nullable=False, comment="基地文档存储路径")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联关系
    template = relationship("Template", back_populates="base_documents")
    contents = relationship("DocumentContent", back_populates="document", cascade="all, delete-orphan")


class DocumentContent(Base):
    """文档内容表"""
    __tablename__ = "document_contents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("base_documents.id"), nullable=False, comment="关联基地文档ID")
    content_type = Column(String(50), nullable=False, comment="内容类型: paragraph/table")
    content_data = Column(Text, nullable=False, comment="内容详细数据(JSON格式)")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关联关系
    document = relationship("BaseDocument", back_populates="contents")


class ExcelTemplate(Base):
    """Excel模板表"""
    __tablename__ = "excel_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="Excel模板名称")
    file_path = Column(String(500), nullable=False, comment="Excel模板文件存储路径")
    status = Column(String(20), default="active", comment="模板状态: active/inactive")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
