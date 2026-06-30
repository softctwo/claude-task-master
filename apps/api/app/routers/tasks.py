from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def list_tasks():
    return {"tasks": []}

@router.get("/tree")
async def get_task_tree():
    """获取任务树"""
    return {"tasks": []}

@router.get("/next")
async def get_next_task():
    """获取推荐下一个任务"""
    return {"next_task": None}

@router.get("/complexity")
async def analyze_complexity():
    """分析任务复杂度"""
    return {"complexity": "TODO"}

@router.get("/{task_id}")
async def get_task(task_id: str):
    return {"task_id": task_id}

@router.put("/{task_id}")
async def update_task(task_id: str):
    return {"task_id": task_id}

@router.post("/{task_id}/expand")
async def expand_task(task_id: str):
    """拆解任务"""
    return {"task_id": task_id, "subtasks": "TODO"}
