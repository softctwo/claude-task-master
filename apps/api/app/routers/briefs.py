"""Brief router with AI PRD generation."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.dependencies import get_current_user, require_manager_or_admin
from app.models import Brief, PRD
from app.schemas import (
    BriefCreate, BriefUpdate, BriefOut, BriefApprove, BriefGeneratePRD,
    PRDOut, PaginationParams, PaginatedResponse,
)
from app.services import brief_service, prd_service, ai_service
from app.utils.pagination import paginate

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_briefs(
    page: int = 1,
    page_size: int = 20,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List briefs with optional filtering."""
    stmt = select(Brief)
    if project_id:
        stmt = stmt.where(Brief.project_id == project_id)
    if status:
        stmt = stmt.where(Brief.status == status)
    stmt = stmt.order_by(desc(Brief.created_at))

    params = PaginationParams(page=page, page_size=page_size)
    return await paginate(
        db, stmt, params,
        transform=lambda b: BriefOut.model_validate(b).model_dump(),
    )


@router.post("", response_model=BriefOut, status_code=status.HTTP_201_CREATED)
async def create_brief(
    brief_in: BriefCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new brief."""
    brief_data = brief_in.model_dump()
    brief_data["owner_id"] = current_user.user_id
    brief = await brief_service.create_brief(db, brief_in, current_user.user_id)
    return BriefOut.model_validate(brief)


@router.get("/{brief_id}", response_model=BriefOut)
async def get_brief(brief_id: str, db: AsyncSession = Depends(get_db)):
    """Get brief by ID."""
    brief = await brief_service.get_brief(db, brief_id)
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    return BriefOut.model_validate(brief)


@router.put("/{brief_id}", response_model=BriefOut)
async def update_brief(
    brief_id: str,
    brief_in: BriefUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update brief."""
    brief = await brief_service.get_brief(db, brief_id)
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    if str(brief.owner_id) != current_user.user_id and current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this brief")
    updated = await brief_service.update_brief(db, brief_id, brief_in, current_user.user_id)
    return BriefOut.model_validate(updated)


@router.delete("/{brief_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brief(
    brief_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """Delete brief (admin/manager only)."""
    brief = await brief_service.get_brief(db, brief_id)
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    await brief_service.delete_brief(db, brief_id, current_user.user_id)
    return None


@router.post("/{brief_id}/generate-prd", response_model=PRDOut)
async def generate_prd_from_brief(
    brief_id: str,
    req: BriefGeneratePRD,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate a PRD from an approved brief using AI."""
    brief = await brief_service.get_brief(db, brief_id)
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    if brief.status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Brief must be approved before generating PRD")

    try:
        result = await ai_service.generate_prd_from_brief(
            title=brief.title,
            background=brief.background,
            problem_statement=brief.problem_statement,
            target_users=brief.target_users,
            goals=brief.goals,
            non_goals=brief.non_goals,
            scope=brief.scope,
            user_stories=brief.user_stories,
            acceptance_criteria=brief.acceptance_criteria,
            constraints=brief.constraints,
            model=getattr(req, "model", None) or "gpt-4o",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI generation failed: {str(e)}")

    prd_data = {
        "brief_id": brief_id,
        "project_id": str(brief.project_id),
        "content_markdown": result.content_markdown,
        "source": "ai_generated",
        "version": 1,
        "generated_by": result.model,
    }
    prd = await prd_service.create_prd(db, prd_service.PRDCreateRequest(**prd_data))
    return PRDOut.model_validate(prd)


@router.post("/{brief_id}/generate-prd-stream")
async def generate_prd_from_brief_stream(
    brief_id: str,
    req: BriefGeneratePRD,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Stream-generate a PRD from an approved brief using AI (SSE)."""
    brief = await brief_service.get_brief(db, brief_id)
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    if brief.status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Brief must be approved before generating PRD")

    async def _event_stream():
        try:
            async for chunk in ai_service.generate_prd_from_brief_stream(
                title=brief.title,
                background=brief.background,
                problem_statement=brief.problem_statement,
                target_users=brief.target_users,
                goals=brief.goals,
                non_goals=brief.non_goals,
                scope=brief.scope,
                user_stories=brief.user_stories,
                acceptance_criteria=brief.acceptance_criteria,
                constraints=brief.constraints,
                model=getattr(req, "model", None) or "gpt-4o",
            ):
                # SSE format: data: <chunk>\n\n
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{brief_id}/approve", response_model=BriefOut)
async def approve_brief(
    brief_id: str,
    req: BriefApprove,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """Approve or reject a brief."""
    brief = await brief_service.get_brief(db, brief_id)
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    updated = await brief_service.approve_brief(db, brief_id, current_user.user_id)
    return BriefOut.model_validate(updated)
