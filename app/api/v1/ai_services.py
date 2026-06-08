"""AI服务API（RAG、Agent等）"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.services.llm_config_service import llm_config_service
from app.services.rag_service import RAGService
from app.services.multi_agent_service import MultiAgentOrchestrator

router = APIRouter(prefix="/api/v1/ai", tags=["AI服务"])

class RAGRequest(BaseModel):
    """RAG请求"""
    user_id: str
    prompt: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7

class RAGWithContextRequest(BaseModel):
    """带上下文的RAG请求"""
    user_id: str
    query: str
    context: str
    max_tokens: Optional[int] = 1000

class AgentRequest(BaseModel):
    """Agent请求"""
    user_id: str
    task_type: str
    evidence: Optional[Dict[str, Any]] = None

class VectorSearchRequest(BaseModel):
    """向量搜索请求"""
    user_id: str
    query_embedding: List[float]
    top_k: Optional[int] = 5

@router.post("/rag/generate")
async def rag_generate(request: RAGRequest):
    """RAG生成响应"""
    llm_config = llm_config_service.get_llm_config(request.user_id)
    if not llm_config or not llm_config.get("baseUrl"):
        raise HTTPException(status_code=400, detail="LLM配置不存在")
    
    rag_service = RAGService(llm_config)
    if not rag_service.is_available():
        raise HTTPException(status_code=500, detail="RAG服务不可用")
    
    response = rag_service.generate_response(
        request.prompt,
        request.max_tokens,
        request.temperature
    )
    
    return {"code": 200, "data": {"response": response}}

@router.post("/rag/chat")
async def rag_chat(request: RAGWithContextRequest):
    """RAG带上下文对话"""
    llm_config = llm_config_service.get_llm_config(request.user_id)
    if not llm_config or not llm_config.get("baseUrl"):
        raise HTTPException(status_code=400, detail="LLM配置不存在")
    
    rag_service = RAGService(llm_config)
    if not rag_service.is_available():
        raise HTTPException(status_code=500, detail="RAG服务不可用")
    
    response = rag_service.chat_with_context(
        request.query,
        request.context,
        request.max_tokens
    )
    
    return {"code": 200, "data": {"response": response}}

@router.post("/agent/run")
async def run_agent(request: AgentRequest):
    """运行多Agent工作流"""
    llm_config = llm_config_service.get_llm_config(request.user_id)
    if not llm_config or not llm_config.get("baseUrl"):
        raise HTTPException(status_code=400, detail="LLM配置不存在")
    
    orchestrator = MultiAgentOrchestrator(llm_config)
    if not orchestrator.is_available():
        raise HTTPException(status_code=500, detail="Agent服务不可用")
    
    result = orchestrator.run(request.task_type, request.evidence)
    
    return {"code": 200, "data": result}

@router.get("/status")
async def get_ai_status(user_id: str):
    """获取AI服务状态"""
    llm_config = llm_config_service.get_llm_config(user_id)
    embedding_config = llm_config_service.get_embedding_config(user_id)
    
    llm_available = bool(llm_config and llm_config.get("baseUrl"))
    embedding_available = bool(embedding_config and embedding_config.get("baseUrl"))
    
    return {
        "code": 200,
        "data": {
            "llm_available": llm_available,
            "embedding_available": embedding_available,
            "llm_configured": llm_available,
            "embedding_configured": embedding_available
        }
    }
