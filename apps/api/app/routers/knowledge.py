from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def list_knowledge_items():
    return {"items": []}

@router.post("")
async def upload_knowledge():
    return {"message": "upload knowledge - TODO"}

@router.get("/search")
async def search_knowledge():
    """语义检索知识库"""
    return {"results": []}

@router.get("/{item_id}")
async def get_knowledge_item(item_id: str):
    return {"item_id": item_id}
