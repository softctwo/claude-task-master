from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()

@router.get("")
async def list_projects():
    """列出项目"""
    return {"projects": []}

@router.post("")
async def create_project():
    """创建项目"""
    return {"message": "create project - TODO"}

@router.get("/{project_id}")
async def get_project(project_id: str):
    """获取项目详情"""
    return {"project_id": project_id}

@router.put("/{project_id}")
async def update_project(project_id: str):
    """更新项目"""
    return {"project_id": project_id}
