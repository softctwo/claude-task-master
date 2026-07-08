"""Pydantic schemas for KnowledgeItem model."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


KnowledgeItemType = Literal["document", "code", "webpage", "note", "image", "video", "api_spec"]
KnowledgeItemEmbeddingStatus = Literal["pending", "processing", "completed", "failed"]
KnowledgeItemVisibility = Literal["project", "workspace", "public", "private"]


class KnowledgeItemBase(BaseModel):
    """Shared base fields for KnowledgeItem schemas."""

    project_id: Optional[str] = Field(default=None, description="Parent project ID (UUID as string)")
    type: KnowledgeItemType = Field(default="document", description="Knowledge item type")
    title: str = Field(min_length=1, max_length=500, description="Knowledge item title")
    source_url: Optional[str] = Field(default=None, description="Original source URL")
    file_path: Optional[str] = Field(default=None, description="Stored file path")
    content_hash: Optional[str] = Field(default=None, max_length=64, description="SHA-256 hash of content")
    parsed_text: Optional[str] = Field(default=None, description="Extracted text content")
    embedding_status: KnowledgeItemEmbeddingStatus = Field(default="pending", description="Vector embedding status")
    visibility: KnowledgeItemVisibility = Field(default="project", description="Access visibility level")


class KnowledgeItemCreate(KnowledgeItemBase):
    """Schema for creating a new knowledge item."""

    model_config = ConfigDict(from_attributes=True)


class KnowledgeItemUpdate(BaseModel):
    """Schema for updating an existing knowledge item."""

    project_id: Optional[str] = Field(default=None, description="Parent project ID")
    type: Optional[KnowledgeItemType] = Field(default=None, description="Knowledge item type")
    title: Optional[str] = Field(default=None, min_length=1, max_length=500, description="Knowledge item title")
    source_url: Optional[str] = Field(default=None, description="Original source URL")
    file_path: Optional[str] = Field(default=None, description="Stored file path")
    content_hash: Optional[str] = Field(default=None, max_length=64, description="SHA-256 hash of content")
    parsed_text: Optional[str] = Field(default=None, description="Extracted text content")
    embedding_status: Optional[KnowledgeItemEmbeddingStatus] = Field(default=None, description="Vector embedding status")
    visibility: Optional[KnowledgeItemVisibility] = Field(default=None, description="Access visibility level")

    model_config = ConfigDict(from_attributes=True)


class KnowledgeItemResponse(KnowledgeItemBase):
    """Schema for knowledge item response."""

    knowledge_id: str = Field(description="Unique knowledge item identifier (UUID as string)")
    created_at: datetime = Field(description="Knowledge item creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class KnowledgeItemList(KnowledgeItemResponse):
    """Schema for knowledge item list items (same as response)."""

    pass
