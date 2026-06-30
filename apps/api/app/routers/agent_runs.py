from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def list_agent_runs():
    return {"runs": []}

@router.post("")
async def create_agent_run():
    return {"message": "create agent run - TODO"}

@router.get("/{run_id}")
async def get_agent_run(run_id: str):
    return {"run_id": run_id}

@router.get("/{run_id}/logs")
async def get_run_logs(run_id: str):
    """获取执行日志流"""
    return {"run_id": run_id, "logs": []}
