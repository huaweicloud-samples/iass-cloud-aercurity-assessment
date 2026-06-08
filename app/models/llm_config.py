from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base

class LLMConfig(Base):
    __tablename__ = "llm_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True, comment="用户ID")
    base_url = Column(String(500), nullable=False, comment="API基础URL")
    model_id = Column(String(100), nullable=False, comment="模型ID")
    api_key = Column(String(500), nullable=False, comment="API密钥(加密存储)")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
