from fastapi import APIRouter

router = APIRouter()

@router.get("/git")
async def list_git_integrations():
    return {"integrations": []}

@router.post("/git")
async def create_git_integration():
    return {"message": "create git integration - TODO"}
