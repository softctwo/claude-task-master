from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def list_prds():
    return {"prds": []}

@router.post("")
async def create_prd():
    return {"message": "create prd - TODO"}

@router.get("/{prd_id}")
async def get_prd(prd_id: str):
    return {"prd_id": prd_id}

@router.put("/{prd_id}")
async def update_prd(prd_id: str):
    return {"prd_id": prd_id}

@router.post("/{prd_id}/generate-tasks")
async def generate_tasks_from_prd(prd_id: str):
    """从 PRD 生成 Taskmaster 任务"""
    return {"prd_id": prd_id, "tasks": "TODO"}
