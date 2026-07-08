# Resoft AI Delivery Studio

## 架构说明

本项目在 `claude-task-master` 基础上扩展，增加了企业级 Web 工作台、后端 API、本地 CLI 同步工具。

## 目录结构

```
├── apps/
│   ├── api/                  # FastAPI 后端服务
│   ├── web/                  # Next.js Web 工作台
│   ├── studio-cli/           # 本地 CLI 同步工具
│   ├── cli/                  # 原 Taskmaster CLI（保留兼容）
│   ├── docs/                 # 文档
│   ├── extension/            # 浏览器扩展
│   └── mcp/                  # MCP Server
├── packages/
│   ├── resoft-types/         # 共享类型定义
│   ├── taskmaster-adapter/   # Taskmaster 适配器
│   ├── tm-core/              # Taskmaster 核心
│   ├── tm-bridge/            # Taskmaster Bridge
│   └── tm-profiles/          # Taskmaster Profiles
├── docker-compose.yml        # 开发环境编排
└── README.md
```

## 快速开始

```bash
# 启动所有服务
docker compose up -d

# 或分别启动
npm run resoft:dev
```
