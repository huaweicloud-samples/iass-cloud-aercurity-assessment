import os

# ============ 数据库配置 ============
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./document_db.sqlite")
# PostgreSQL生产示例: postgresql+psycopg2://user:pass@localhost:5432/audit_db

# ============ JWT认证配置 ============
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# ============ 文件上传配置 ============
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
TEMPLATE_DIR = os.path.join(UPLOAD_DIR, "templates")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = [".docx", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".pdf"]

# ============ MinIO对象存储配置 ============
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "audit-materials")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# ============ Milvus向量库配置 ============
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
MILVUS_COLLECTION = "benchmark_embeddings"
MILVUS_DIMENSION = 1536

# ============ Redis缓存配置 ============
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ============ LLM默认配置 ============
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
LLM_EMBEDDING_MODEL = os.getenv("LLM_EMBEDDING_MODEL", "text-embedding-ada-002")

# ============ 大模型配置系统 ============
AI_MODEL_API_KEY = os.getenv("AI_MODEL_API_KEY", "your-openai-api-key-here")
AI_MODEL_BASE_URL = os.getenv("AI_MODEL_BASE_URL", "https://api.openai.com/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "1024"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.8"))
RERANK_MODEL = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-base")
RERANK_ENABLED = os.getenv("RERANK_ENABLED", "True").lower() == "true"
RRF_K = int(os.getenv("RRF_K", "60"))

# ============ 配置文件目录 ============
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "configs")

# ============ OCR配置 ============
OCR_ENGINE = os.getenv("OCR_ENGINE", "paddleocr")  # paddleocr / tesseract
OCR_CACHE_DAYS = 30

# ============ 日志配置 ============
LOG_DIR = os.getenv("LOG_DIR", "logs")

# ============ CORS配置 ============
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

# ============ 确保目录存在 ============
os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
