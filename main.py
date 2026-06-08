from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import traceback
from datetime import datetime

from app.database import init_db
from config import CORS_ORIGINS, LOG_DIR

# V1 API路由
from app.api.v1.auth import router as auth_router
from app.api.v1.items import router as items_router
from app.api.v1.materials import router as materials_router
from app.api.v1.audit import router as audit_router
from app.api.v1.benchmark_guide import (
    router_benchmark, router_guide, router_llm
)
from app.api.v1.account_management import router_base, router_user
from app.api.v1.declaration_templates import router as declaration_templates_router
from app.api.v1.standard_templates import router as standard_templates_router
from app.api.v1.risk_identification import router as risk_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.sensitive_monitor import router as sensitive_router
from app.api.v1.llm_config import router as llm_config_router
from app.api.v1.ai_services import router as ai_services_router
from app.api.v1.progress import router as progress_router

# 兼容旧版路由
from app.api.documents import router as documents_router
from app.api.base_document_editor import router as base_document_router
from app.api.excel_template_upload import router as excel_template_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"{LOG_DIR}/app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="云计算服务安全评估智能预审Agent",
    description="基于大模型与Agent智能编排的GB/T 31168-2023安全评估预审系统",
    version="1.0.0"
)

# CORS跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 注册V1 API路由 ============
app.include_router(auth_router)
app.include_router(items_router)
app.include_router(materials_router)
app.include_router(audit_router)
app.include_router(router_benchmark)
app.include_router(router_base)
app.include_router(router_user)
app.include_router(router_guide)
app.include_router(router_llm)
app.include_router(declaration_templates_router)
app.include_router(standard_templates_router)
app.include_router(risk_router)
app.include_router(evidence_router)
app.include_router(sensitive_router)
app.include_router(llm_config_router)
app.include_router(ai_services_router)
app.include_router(progress_router)

# 兼容旧版路由
app.include_router(documents_router)
app.include_router(base_document_router)
app.include_router(excel_template_router)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": f"服务器内部错误: {str(exc)}", "data": None}
    )


# 启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("系统启动中...")
    init_db()
    logger.info("数据库初始化完成")


# 健康检查接口
@app.get("/api/health", tags=["系统"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
