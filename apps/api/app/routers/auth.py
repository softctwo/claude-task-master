from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()

@router.post("/login")
async def login():
    """用户登录"""
    return {"message": "login endpoint - TODO"}

@router.post("/register")
async def register():
    """用户注册"""
    return {"message": "register endpoint - TODO"}

@router.get("/me")
async def get_current_user():
    """获取当前用户信息"""
    return {"message": "me endpoint - TODO"}
