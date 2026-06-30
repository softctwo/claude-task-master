from fastapi import APIRouter

router = APIRouter()

@router.get("/logs")
async def list_audit_logs():
    """列出审计日志"""
    return {"logs": []}
