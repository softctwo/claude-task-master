"""AI Chat router for general AI assistant interactions."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.services import ai_service
from app.schemas import UserOut

router = APIRouter()


class ChatRequest:
    """Request body for chat completion."""
    def __init__(self, messages: List[dict], model: str = "gpt-4o", temperature: float = 0.7):
        self.messages = messages
        self.model = model
        self.temperature = temperature


@router.post("/chat")
async def chat(
    req: dict,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):
    """General AI chat completion endpoint."""
    messages = req.get("messages", [])
    model = req.get("model", "gpt-4o")
    temperature = req.get("temperature", 0.7)

    if not messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Messages are required",
        )

    try:
        chat_messages = [
            ai_service.ChatMessage(role=m["role"], content=m["content"])
            for m in messages
        ]
        result = await ai_service.chat_completion(
            messages=chat_messages,
            model=model,
            temperature=temperature,
        )
        return {"content": result.content, "model": result.model}
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
