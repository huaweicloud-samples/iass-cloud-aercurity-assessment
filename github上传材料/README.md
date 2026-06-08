# 云计算服务安全评估智能预审Agent

基于大模型与 Agent 智能编排的 GB/T 31168-2023 安全评估预审系统。

## 项目简介

本系统依据国家标准 **GB/T 31168-2023**（信息安全技术 云计算服务安全能力要求），面向云计算服务安全评估场景，构建基于大模型与多 Agent 智能编排的自动化预审系统，实现：

- **智能审核**：5 个专业 Agent 组成状态机工作流，自动完成"分拣→解读→审查→诊断→引导"全链路审核
- **标杆参照**：RAG 检索增强，以已通过评估的标杆基地材料作为审核参照
- **证据对比**：多维度加权评分算法，智能对比举证材料与标准要求的符合度
- **风险识别**：5 步向导式采集，自动评估综合风险等级
- **交互引导**：审核不通过时自动定位根因，生成精准整改建议和填报引导

## 技术栈

### 后端

| 分类 | 技术 | 版本 | 用途 |
|------|------|------|------|
| Web 框架 | FastAPI | 0.104.1 | 异步 API 服务 |
| 运行时 | Uvicorn | 0.24.0 | ASGI 服务器 |
| ORM | SQLAlchemy | 2.0.23 | 数据库 ORM |
| 数据库 | SQLite / PostgreSQL | - | 开发 / 生产 |
| AI 编排 | LangGraph | 0.0.60 | 多 Agent 工作流编排 |
| AI 框架 | LangChain | 0.2.1 | LLM 调用链 |
| LLM SDK | OpenAI | 1.30.0 | 兼容 OpenAI 接口的大模型调用 |
| 向量检索 | FAISS / pymilvus | 1.7.4 / 2.4.9 | 向量相似度检索 |
| OCR | PaddleOCR + PaddlePaddle | 2.7.3 / 2.6.2 | 图像文字识别 |
| 图像处理 | OpenCV | 4.6.0 | 图像预处理 |
| PDF 处理 | PyMuPDF | 1.24.3 | PDF 文字提取 |
| 文档处理 | python-docx | 1.1.0 | Word 文档读写 |
| 认证 | python-jose + passlib | 3.3.0 / 1.7.4 | JWT + bcrypt |
| 对象存储 | MinIO | 7.2.7 | 文件对象存储 |
| 缓存 | Redis | 5.0.4 | 数据缓存 |

### 前端

| 分类 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 框架 | React | 19.2.6 | UI 渲染 |
| 语言 | TypeScript | 6.0.2 | 类型安全 |
| 构建 | Vite | 8.0.12 | 开发构建 |
| UI 库 | Ant Design | 6.4.3 | 企业级组件库 |
| 样式 | Tailwind CSS | 4.3.0 | 原子化 CSS |
| 状态管理 | Zustand | 5.0.13 | 全局状态 |
| 数据请求 | Axios + React Query | 1.16.1 / 5.100.11 | HTTP 客户端 + 服务端状态缓存 |

### AI 模型

| 模型类型 | 默认模型 | 用途 |
|---------|---------|------|
| LLM | qwen3.5-2b / GPT-4 | 文本生成、审核推理 |
| Embedding | bge-m3 | 文本向量化 |
| Rerank | bge-reranker-v2-m3 | 检索结果重排序 |
| 多模态 | qwen3.5-2b | 图像理解 |

## 项目结构

```
yunpinggu/
├── main.py                          # 后端入口 (FastAPI)
├── config.py                        # 全局配置
├── .env                             # 环境变量
├── requirements.txt                 # Python 依赖
├── start_backend.bat                # Windows 启动脚本
│
├── app/                             # 后端核心应用
│   ├── database.py                  # 数据库初始化与会话管理
│   ├── core/
│   │   └── auth.py                  # JWT 认证 + 角色权限
│   ├── agents/
│   │   └── audit_workflow.py        # Agent 审核工作流 (5 个 Agent 节点)
│   ├── api/
│   │   └── v1/                      # V1 版本 API (16 个路由模块)
│   │       ├── auth.py              # 认证登录
│   │       ├── items.py             # 标准条目管理
│   │       ├── materials.py         # 材料管理
│   │       ├── audit.py             # 智能审核
│   │       ├── evidence.py          # 证据对比
│   │       ├── risk_identification.py  # 风险识别
│   │       ├── benchmark_guide.py   # 标杆管理 + 交互引导 + LLM 配置
│   │       ├── ai_services.py       # AI 服务 (RAG/Agent)
│   │       ├── sensitive_monitor.py # 敏感信息监测
│   │       ├── progress.py          # 进度看板
│   │       └── ...
│   ├── models/                      # 数据模型 (User/Item/Base/Material/AuditRecord/...)
│   ├── schemas/                     # Pydantic 数据校验模式
│   ├── services/                    # 业务服务层
│   │   ├── llm_service.py           # LLM 调用 + Prompt 模板
│   │   ├── multi_agent_service.py   # 多 Agent 编排 (LangGraph)
│   │   ├── rag_service.py           # RAG 检索增强
│   │   ├── ocr_service.py           # OCR 识别 (PaddleOCR)
│   │   ├── vector_store.py          # 向量存储
│   │   └── llm_config_service.py    # LLM 配置管理
│   └── utils/
│       └── document_handler.py      # 文档处理工具
│
├── yunping/frontend/                # 前端项目
│   ├── src/
│   │   ├── App.tsx                  # 根组件 (认证 + 布局切换)
│   │   ├── api/                     # API 接口层 (Axios + React Query)
│   │   ├── store/                   # 状态管理 (Zustand)
│   │   ├── components/              # 公共组件 (Layout/文档渲染器/风险识别弹窗)
│   │   └── pages/                   # 页面组件 (10 个业务页面)
│   └── vite.config.ts              # Vite 构建配置
│
├── configs/                         # 配置文件目录
│   └── llm_config_admin.json        # 管理员 LLM 配置
├── uploads/                         # 文件上传目录
│   ├── evidence/                    # 证据材料
│   └── templates/                   # 模板文件
└── logs/                            # 日志目录
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- PaddlePaddle GPU（可选，用于加速 OCR）

### 1. 后端启动

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 AI_MODEL_API_KEY 等配置

# 启动后端服务
python main.py
```

后端服务启动在 `http://localhost:8000`，API 文档访问 `http://localhost:8000/docs`。

Windows 用户可直接双击 `start_backend.bat` 一键启动。

### 2. 前端启动

```bash
cd yunping/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端开发服务器启动在 `http://localhost:5173`，自动代理 `/api` 请求到后端。

### 3. 生产构建

```bash
# 前端构建
cd yunping/frontend
npm run build
# 产物在 dist/ 目录，由 Nginx 托管
```

## 核心架构

### Agent 智能编排工作流

```
初始 → Dispatcher(分拣) → Interpreter(解读) → Evidence(审查) → [得分≥80] → 通过
                                                          → [得分<80] → Diagnosis(诊断) → Guide(引导)
```

| Agent | 职责 |
|-------|------|
| **DispatcherAgent** | 分析条目类型，分配审核路径（视觉优先 / 文本优先 / 标准） |
| **InterpreterAgent** | RAG 检索标杆材料，拆解合规检查要素 |
| **EvidenceAgent** | 文本 / 视觉 / 关联性三位一体核验，输出合规得分 |
| **DiagnosisAgent** | 审核不通过时定位根因，输出整改方案 |
| **GuideAgent** | 生成补充问题、填报草稿、证据材料清单 |

### 证据对比算法

```
最终得分 = 文件命名相似度 × 0.2 + 内容识别相似度 × 0.8
审核判定: 最终得分 ≥ 0.8 → 满足
```

### 角色权限

| 角色 | 权限 |
|------|------|
| `sys_admin` | 系统管理员，最高权限 |
| `eval_admin` | 评估管理员，管理标杆 / 基地 / 审核 |
| `base_user` | 基地申报人员，仅操作关联基地数据 |
| `auditor` | 审核专家，只读权限 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AI_MODEL_API_KEY` | - | 大模型 API Key |
| `AI_MODEL_BASE_URL` | `https://api.openai.com/v1` | 大模型 API 地址 |
| `EMBEDDING_MODEL` | `text-embedding-ada-002` | Embedding 模型 |
| `VECTOR_DIMENSION` | `1024` | 向量维度 |
| `SIMILARITY_THRESHOLD` | `0.8` | 相似度阈值 |
| `RERANK_MODEL` | `BAAI/bge-reranker-base` | Rerank 模型 |
| `RERANK_ENABLED` | `True` | 是否启用 Rerank |
| `DATABASE_URL` | `sqlite:///./document_db.sqlite` | 数据库连接串 |
| `JWT_SECRET_KEY` | `change-this-secret-in-production` | JWT 密钥（生产环境务必修改） |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO 对象存储地址 |
| `MILVUS_HOST` | `localhost` | Milvus 向量库地址 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 缓存地址 |

## API 接口

所有接口统一使用 `/api/v1/` 前缀，详细文档请访问 Swagger UI：`http://localhost:8000/docs`

| 模块 | 前缀 | 核心接口 |
|------|------|---------|
| 认证 | `/api/v1/auth` | login / register / me |
| 标准条目 | `/api/v1/items` | CRUD |
| 智能审核 | `/api/v1/audit` | run / result / results |
| 证据对比 | `/api/v1/evidence` | uploadList / uploadMaterial / compare / audit |
| 风险识别 | `/api/v1/risk` | check / my / base / save / all |
| 标杆管理 | `/api/v1/benchmarks` | CRUD + uploadMaterial |
| 交互引导 | `/api/v1/guide` | runGuide |
| AI 服务 | `/api/v1/ai` | ragGenerate / ragChat / runAgent / status |
| LLM 配置 | `/api/v1/llm-configs` | get / save / providers |
| 敏感监测 | `/api/v1/sensitive` | scan / results |
| 进度看板 | `/api/v1/progress` | getProgressOverview |

## 部署

### 开发环境

```
前端: Vite Dev Server (localhost:5173) → 代理 /api → 后端
后端: Uvicorn (localhost:8000) → SQLite + 本地文件存储
```

### 生产环境

```
前端: Nginx 静态资源托管 → 反向代理 /api → 后端
后端: Uvicorn + Gunicorn → PostgreSQL + MinIO + Milvus + Redis
```

生产环境需修改以下配置：
- `DATABASE_URL` 切换为 PostgreSQL 连接串
- `JWT_SECRET_KEY` 设置为强随机密钥
- 启用 MinIO 对象存储替代本地文件系统
- 启用 Milvus 向量库替代内存向量存储
- 启用 Redis 缓存

## License

Private - 内部项目
