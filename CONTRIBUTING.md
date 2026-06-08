# 贡献指南

感谢你对云计算服务安全评估智能预审Agent项目的关注！本文档将帮助你了解如何参与项目贡献。

## 行为准则

- 尊重所有贡献者，保持专业和友善的沟通态度
- 聚焦技术问题本身，避免人身攻击或不当言论
- 尊重不同观点和经验，提供建设性反馈

## 环境准备

### 后端开发环境

```bash
# 创建并激活虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入必要配置

# 启动后端
python main.py
```

### 前端开发环境

```bash
cd yunping/frontend
npm install
npm run dev
```

## 开发流程

### 1. 创建分支

```bash
# 从 main 分支创建功能分支
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# 修复分支命名示例
git checkout -b fix/your-fix-name
```

分支命名规范：

| 类型 | 前缀 | 示例 |
|------|------|------|
| 新功能 | `feature/` | `feature/add-export-function` |
| 缺陷修复 | `fix/` | `fix/audit-score-calculation` |
| 文档更新 | `docs/` | `docs/update-api-reference` |
| 重构 | `refactor/` | `refactor/simplify-agent-workflow` |

### 2. 编码规范

#### 后端（Python）

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 代码风格
- 使用类型注解，保持与现有代码风格一致
- API 路由放在 `app/api/v1/` 下，业务逻辑放在 `app/services/` 下
- 数据模型放在 `app/models/`，Pydantic 校验模式放在 `app/schemas/`
- 新增 API 端点需在 `main.py` 中注册路由

#### 前端（TypeScript / React）

- 遵循 ESLint 配置，提交前执行 `npm run lint` 检查
- 页面组件放在 `src/pages/` 下，每个页面一个独立目录
- 公共组件放在 `src/components/` 下
- API 接口定义在 `src/api/index.ts` 中统一管理
- 全局状态通过 Zustand store（`src/store/index.ts`）管理

#### 通用规范

- 提交信息使用中文或英文，格式清晰，说明改动目的
- 不引入不必要的依赖，不过度设计
- 不添加与本次改动无关的代码清理或重构

### 3. 提交代码

```bash
git add .
git commit -m "feat: 添加XX功能"
```

提交信息格式：

| 前缀 | 用途 |
|------|------|
| `feat:` | 新功能 |
| `fix:` | 缺陷修复 |
| `docs:` | 文档更新 |
| `style:` | 代码格式调整（不影响逻辑） |
| `refactor:` | 重构 |
| `test:` | 测试相关 |
| `chore:` | 构建/工具/依赖变更 |

### 4. 提交 Pull Request

- PR 标题简明扼要，说明改动内容
- PR 描述包含：改动目的、涉及模块、测试情况
- 关联相关 Issue（如有）
- 确保本地测试通过后再提交

## 项目结构参考

```
app/
├── agents/          # Agent 工作流编排
├── api/v1/          # API 路由（按业务模块划分）
├── core/            # 核心模块（认证等）
├── models/          # 数据模型
├── schemas/         # Pydantic 校验模式
├── services/        # 业务服务层
└── utils/           # 工具函数

yunping/frontend/src/
├── api/             # API 接口定义
├── components/      # 公共组件
├── pages/           # 页面组件
└── store/           # 状态管理
```

## 报告问题

提交 Issue 时请包含以下信息：

- 问题描述及复现步骤
- 期望行为与实际行为
- 运行环境（操作系统、Python 版本、Node.js 版本）
- 相关日志或截图

## 许可证

本项目采用 [MIT License](LICENSE)，贡献的代码将遵循同一许可证。
