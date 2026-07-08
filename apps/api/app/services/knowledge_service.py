"""Knowledge Service - 知识库 CRUD + 语义检索"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, and_, func, text, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KnowledgeItem


# ────────────────────────────────
# Pydantic Schemas
# ────────────────────────────────

class KnowledgeItemCreate(BaseModel):
    project_id: Optional[str] = None
    type: Literal["document", "code", "link", "note", "image", "video"] = "document"
    title: str = Field(..., min_length=1, max_length=500)
    source_url: Optional[str] = None
    file_path: Optional[str] = None
    content_hash: Optional[str] = None
    parsed_text: Optional[str] = None
    visibility: Literal["project", "workspace", "public", "private"] = "project"


class KnowledgeItemUpdate(BaseModel):
    type: Optional[Literal["document", "code", "link", "note", "image", "video"]] = None
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    source_url: Optional[str] = None
    file_path: Optional[str] = None
    content_hash: Optional[str] = None
    parsed_text: Optional[str] = None
    embedding_status: Optional[Literal["pending", "processing", "completed", "failed"]] = None
    visibility: Optional[Literal["project", "workspace", "public", "private"]] = None


class KnowledgeItemOut(BaseModel):
    knowledge_id: str
    project_id: Optional[str] = None
    type: Literal["document", "code", "link", "note", "image", "video"]
    title: str
    source_url: Optional[str] = None
    file_path: Optional[str] = None
    content_hash: Optional[str] = None
    parsed_text: Optional[str] = None
    embedding_status: Literal["pending", "processing", "completed", "failed"]
    visibility: Literal["project", "workspace", "public", "private"]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeItemListResponse(BaseModel):
    items: List[KnowledgeItemOut]
    total: int
    page: int
    page_size: int


class SemanticSearchResult(BaseModel):
    knowledge_id: str
    title: str
    type: str
    parsed_text: Optional[str] = None
    source_url: Optional[str] = None
    similarity_score: float

    model_config = ConfigDict(from_attributes=True)


class KnowledgeStats(BaseModel):
    total_items: int
    by_type: Dict[str, int]
    by_embedding_status: Dict[str, int]
    by_visibility: Dict[str, int]


# ────────────────────────────────
# Service Functions
# ────────────────────────────────

async def create_knowledge_item(
    db: AsyncSession, data: KnowledgeItemCreate
) -> KnowledgeItemOut:
    """创建知识库条目"""
    item = KnowledgeItem(
        project_id=UUID(data.project_id) if data.project_id else None,
        type=data.type,
        title=data.title,
        source_url=data.source_url,
        file_path=data.file_path,
        content_hash=data.content_hash,
        parsed_text=data.parsed_text,
        visibility=data.visibility,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return KnowledgeItemOut.model_validate(item)


async def get_knowledge_item(
    db: AsyncSession, knowledge_id: str
) -> Optional[KnowledgeItemOut]:
    """根据 ID 获取知识库条目"""
    result = await db.execute(
        select(KnowledgeItem).where(KnowledgeItem.knowledge_id == UUID(knowledge_id))
    )
    item = result.scalar_one_or_none()
    if item is None:
        return None
    return KnowledgeItemOut.model_validate(item)


async def list_knowledge_items(
    db: AsyncSession,
    project_id: Optional[str] = None,
    item_type: Optional[str] = None,
    visibility: Optional[str] = None,
    embedding_status: Optional[str] = None,
    search_query: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> KnowledgeItemListResponse:
    """列出知识库条目，支持过滤和全文搜索"""
    query = select(KnowledgeItem)
    filters = []

    if project_id:
        filters.append(KnowledgeItem.project_id == UUID(project_id))
    if item_type:
        filters.append(KnowledgeItem.type == item_type)
    if visibility:
        filters.append(KnowledgeItem.visibility == visibility)
    if embedding_status:
        filters.append(KnowledgeItem.embedding_status == embedding_status)

    if filters:
        query = query.where(and_(*filters))

    # Full-text search on title and parsed_text
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.where(
            or_(
                KnowledgeItem.title.ilike(search_pattern),
                KnowledgeItem.parsed_text.ilike(search_pattern),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    query = query.order_by(KnowledgeItem.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return KnowledgeItemListResponse(
        items=[KnowledgeItemOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


async def update_knowledge_item(
    db: AsyncSession, knowledge_id: str, data: KnowledgeItemUpdate
) -> Optional[KnowledgeItemOut]:
    """更新知识库条目"""
    result = await db.execute(
        select(KnowledgeItem).where(KnowledgeItem.knowledge_id == UUID(knowledge_id))
    )
    item = result.scalar_one_or_none()
    if item is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)
    return KnowledgeItemOut.model_validate(item)


async def delete_knowledge_item(db: AsyncSession, knowledge_id: str) -> bool:
    """删除知识库条目"""
    result = await db.execute(
        select(KnowledgeItem).where(KnowledgeItem.knowledge_id == UUID(knowledge_id))
    )
    item = result.scalar_one_or_none()
    if item is None:
        return False

    await db.delete(item)
    await db.commit()
    return True


async def update_embedding_status(
    db: AsyncSession,
    knowledge_id: str,
    status: Literal["pending", "processing", "completed", "failed"],
) -> Optional[KnowledgeItemOut]:
    """更新知识库条目的嵌入状态"""
    result = await db.execute(
        select(KnowledgeItem).where(KnowledgeItem.knowledge_id == UUID(knowledge_id))
    )
    item = result.scalar_one_or_none()
    if item is None:
        return None

    item.embedding_status = status
    await db.commit()
    await db.refresh(item)
    return KnowledgeItemOut.model_validate(item)


async def semantic_search(
    db: AsyncSession,
    query_embedding: List[float],
    project_id: Optional[str] = None,
    top_k: int = 10,
    similarity_threshold: float = 0.7,
) -> List[SemanticSearchResult]:
    """语义检索知识库条目

    使用 pgvector 进行向量相似度搜索。需要数据库已配置 pgvector 扩展和 embedding 向量列。
    如果 embedding 列不存在，回退到基于文本的搜索。
    """
    # Check if embedding column exists (pgvector)
    try:
        # Try vector similarity search using pgvector
        embedding_str = ",".join(str(v) for v in query_embedding)
        sql = text(f"""
            SELECT
                knowledge_id,
                title,
                type,
                parsed_text,
                source_url,
                1 - (embedding <=> '[{embedding_str}]'::vector) as similarity_score
            FROM knowledge_items
            WHERE embedding IS NOT NULL
            AND 1 - (embedding <=> '[{embedding_str}]'::vector) >= :threshold
            {f"AND project_id = :project_id" if project_id else ""}
            ORDER BY similarity_score DESC
            LIMIT :limit
        """)

        params = {
            "threshold": similarity_threshold,
            "limit": top_k,
        }
        if project_id:
            params["project_id"] = UUID(project_id)

        result = await db.execute(sql, params)
        rows = result.fetchall()

        return [
            SemanticSearchResult(
                knowledge_id=str(row.knowledge_id),
                title=row.title,
                type=row.type,
                parsed_text=row.parsed_text,
                source_url=row.source_url,
                similarity_score=round(float(row.similarity_score), 4),
            )
            for row in rows
        ]
    except Exception:
        # Fallback to text-based search if pgvector is not available
        return await _text_based_search(db, project_id, top_k)


async def _text_based_search(
    db: AsyncSession,
    project_id: Optional[str] = None,
    limit: int = 10,
) -> List[SemanticSearchResult]:
    """基于文本的回退搜索（当 pgvector 不可用时）"""
    query = select(KnowledgeItem).where(
        KnowledgeItem.parsed_text.isnot(None)
    )

    if project_id:
        query = query.where(KnowledgeItem.project_id == UUID(project_id))

    query = query.order_by(KnowledgeItem.created_at.desc()).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return [
        SemanticSearchResult(
            knowledge_id=str(item.knowledge_id),
            title=item.title,
            type=item.type,
            parsed_text=item.parsed_text,
            source_url=item.source_url,
            similarity_score=1.0,  # Default score for fallback
        )
        for item in items
    ]


async def get_knowledge_stats(
    db: AsyncSession, project_id: Optional[str] = None
) -> KnowledgeStats:
    """获取知识库统计信息"""
    query = select(KnowledgeItem)
    if project_id:
        query = query.where(KnowledgeItem.project_id == UUID(project_id))

    result = await db.execute(query)
    items = result.scalars().all()

    by_type: Dict[str, int] = {}
    by_embedding_status: Dict[str, int] = {}
    by_visibility: Dict[str, int] = {}

    for item in items:
        by_type[item.type] = by_type.get(item.type, 0) + 1
        by_embedding_status[item.embedding_status] = by_embedding_status.get(item.embedding_status, 0) + 1
        by_visibility[item.visibility] = by_visibility.get(item.visibility, 0) + 1

    return KnowledgeStats(
        total_items=len(items),
        by_type=by_type,
        by_embedding_status=by_embedding_status,
        by_visibility=by_visibility,
    )


async def bulk_create_knowledge_items(
    db: AsyncSession, items: List[KnowledgeItemCreate]
) -> List[KnowledgeItemOut]:
    """批量创建知识库条目"""
    created = []
    for data in items:
        item = KnowledgeItem(
            project_id=UUID(data.project_id) if data.project_id else None,
            type=data.type,
            title=data.title,
            source_url=data.source_url,
            file_path=data.file_path,
            content_hash=data.content_hash,
            parsed_text=data.parsed_text,
            visibility=data.visibility,
        )
        db.add(item)
        created.append(item)

    await db.commit()
    for item in created:
        await db.refresh(item)

    return [KnowledgeItemOut.model_validate(i) for i in created]


async def get_items_by_type(
    db: AsyncSession,
    item_type: Literal["document", "code", "link", "note", "image", "video"],
    project_id: Optional[str] = None,
    limit: int = 100,
) -> List[KnowledgeItemOut]:
    """按类型获取知识库条目"""
    query = select(KnowledgeItem).where(KnowledgeItem.type == item_type)
    if project_id:
        query = query.where(KnowledgeItem.project_id == UUID(project_id))
    query = query.limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()
    return [KnowledgeItemOut.model_validate(i) for i in items]
