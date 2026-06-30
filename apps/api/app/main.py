from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.routers import auth, projects, briefs, prds, tasks, agent_runs, knowledge, audit, integrations
from app.celery_app import celery_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Resoft AI Delivery Studio API",
    description="企业级 AI 研发交付协同平台后端 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["项目"])
app.include_router(briefs.router, prefix="/api/v1/briefs", tags=["Brief"])
app.include_router(prds.router, prefix="/api/v1/prds", tags=["PRD"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["任务"])
app.include_router(agent_runs.router, prefix="/api/v1/agent-runs", tags=["Agent 执行"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["知识库"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["审计"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["集成"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root():
    return {"message": "Resoft AI Delivery Studio API", "docs": "/docs"}
