"""AgentRun router."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.dependencies import get_current_user, require_developer_or_above
from app.models import AgentRun
from app.schemas import AgentRunCreate, AgentRunUpdate, AgentRunOut, AgentRunLogs, PaginationParams, PaginatedResponse
from app.services import agent_run_service
from app.utils.pagination import paginate

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_agent_runs(
    page: int = 1,
    page_size: int = 20,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List agent runs with optional filtering."""
    stmt = select(AgentRun)
    if project_id:
        stmt = stmt.where(AgentRun.project_id == project_id)
    if task_id:
        stmt = stmt.where(AgentRun.task_id == task_id)
    if status:
        stmt = stmt.where(AgentRun.status == status)
    stmt = stmt.order_by(desc(AgentRun.created_at))

    params = PaginationParams(page=page, page_size=page_size)
    return await paginate(
        db, stmt, params,
        transform=lambda r: AgentRunOut.model_validate(r).model_dump(),
    )


@router.post("", response_model=AgentRunOut, status_code=status.HTTP_201_CREATED)
async def create_agent_run(
    run_in: AgentRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new agent run."""
    run = await agent_run_service.create(db, run_in.model_dump())
    return AgentRunOut.model_validate(run)


@router.get("/{run_id}", response_model=AgentRunOut)
async def get_agent_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Get agent run by ID."""
    run = await agent_run_service.get(db, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
    return AgentRunOut.model_validate(run)


@router.put("/{run_id}", response_model=AgentRunOut)
async def update_agent_run(
    run_id: str,
    run_in: AgentRunUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update agent run."""
    run = await agent_run_service.get(db, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
    updated = await agent_run_service.update(db, run, run_in.model_dump(exclude_unset=True))
    return AgentRunOut.model_validate(updated)


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_developer_or_above),
):
    """Delete agent run."""
    run = await agent_run_service.get(db, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
    await agent_run_service.delete(db, run)
    return None


@router.get("/{run_id}/logs", response_model=AgentRunLogs)
async def get_run_logs(run_id: str, db: AsyncSession = Depends(get_db)):
    """Get execution logs for an agent run."""
    run = await agent_run_service.get(db, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
    return AgentRunLogs(run_id=run_id, logs=run.logs or "")
