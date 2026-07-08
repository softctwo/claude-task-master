# Resoft AI Delivery Studio

> 基于 claude-task-master 的企业级 AI 研发交付协同平台

## 项目概述

Resoft AI Delivery Studio 是面向中软融鑫内部的 AI 研发交付协同平台。它以开源项目 `claude-task-master` 作为本地任务规划和 AI 执行底座，在其上构建企业级 Web 工作台、团队协作、知识上下文、执行过程可视化、权限审计和项目管理集成能力。

## 核心链路

```text
业务需求 -> 需求澄清 -> PRD/Brief -> Taskmaster 任务树 -> AI/人工执行 -> 代码/文档/交付物 -> 复盘沉淀
```

## 技术架构

```text
Web Studio
  -> API Server (FastAPI)
    -> Auth / RBAC
    -> Brief / PRD / Task / Knowledge Service
    -> Taskmaster Adapter
    -> Agent Run Service
    -> Context Graph Service
    -> Integration Service
  -> PostgreSQL + pgvector
  -> Redis Queue
  -> Object Storage
  -> Git Provider
  -> Model Providers
  -> Local CLI / Runner
```

## 项目结构

```
claude-task-master/
├── apps/
│   ├── cli/                  # 原 Taskmaster CLI（保留兼容）
│   ├── web/                  # Resoft Web Studio (Next.js)
│   ├── api/                  # Resoft API Server (FastAPI)
│   ├── studio-cli/           # Resoft 本地 CLI 同步工具
│   ├── docs/                 # 文档
│   ├── extension/            # 浏览器扩展
│   └── mcp/                  # MCP Server
├── packages/
│   ├── tm-core/              # Taskmaster 核心（保留）
│   ├── tm-bridge/            # Taskmaster Bridge（保留）
│   ├── tm-profiles/          # Taskmaster Profiles（保留）
│   ├── resoft-types/         # Resoft 共享类型定义
│   └── taskmaster-adapter/   # Taskmaster 适配器
├── docker-compose.yml        # 开发环境编排
└── README.md
```

## 快速开始

### 环境要求

- Node.js >= 20
- Python >= 3.12
- Docker + Docker Compose
- PostgreSQL 16 + pgvector
- Redis 7

### 启动开发环境

```bash
# 1. 克隆仓库
git clone https://github.com/softctwo/claude-task-master.git
cd claude-task-master
git checkout feature/resoft-studio

# 2. 启动基础设施（PostgreSQL + Redis + Celery）
docker compose up -d postgres redis

# 3. 启动后端 API
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 4. 启动前端（新终端）
cd apps/web
npm install
npm run dev

# 5. 启动 Celery Worker（新终端）
cd apps/api
celery -A app.celery_app worker --loglevel=info
```

访问 http://localhost:3000 打开 Web Studio。

## 核心功能

### MVP 阶段（第一阶段）

- [x] 用户登录和项目管理
- [x] Brief 创建、编辑、审批
- [x] Brief 生成 PRD
- [x] PRD 调用 Taskmaster 生成任务
- [x] 任务树、看板、详情和依赖展示
- [x] Taskmaster 复杂度分析和 next task 展示
- [x] 本地 CLI 同步 `.taskmaster/`
- [x] 基础知识文档上传和检索
- [x] Agent Run 日志记录（手动/本地执行）
- [x] 操作审计

### 后续阶段

- [ ] 多人评论、审批、变更记录和版本管理
- [ ] Git 平台、Issue 系统集成
- [ ] 任务执行过程实时可视化
- [ ] 项目级知识图谱和上下文检索
- [ ] 云端/内网 Agent 沙箱执行
- [ ] 多 Agent 并行任务、分支策略、PR 自动生成
- [ ] 交付指标、团队效能、AI 产能分析

## 许可证

本项目基于 `claude-task-master` (MIT + Commons Clause) 进行内部扩展开发。

内部使用阶段保留原始许可证声明。Resoft 的商业价值定义在企业协作、知识库、权限、审计、私有部署、行业模板和 Agent 编排。

详见 [LICENSE](LICENSE)。

## 贡献

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

*Resoft AI Delivery Studio - 让 AI 交付更有序*
