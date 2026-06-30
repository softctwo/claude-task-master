from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def list_briefs():
    return {"briefs": []}

@router.post("")
async def create_brief():
    return {"message": "create brief - TODO"}

@router.get("/{brief_id}")
async def get_brief(brief_id: str):
    return {"brief_id": brief_id}

@router.put("/{brief_id}")
async def update_brief(brief_id: str):
    return {"brief_id": brief_id}

@router.post("/{brief_id}/generate-prd")
async def generate_prd_from_brief(brief_id: str):
    """从 Brief 生成 PRD"""
    return {"brief_id": brief_id, "prd": "TODO"}

@router.post("/{brief_id}/approve")
async def approve_brief(brief_id: str):
    """审批 Brief"""
    return {"brief_id": brief_id, "status": "approved"}
