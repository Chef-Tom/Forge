"""Data models for Forge projects."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """Project lifecycle status."""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ProjectRules(BaseModel):
    """Constraints the LLM must follow for this project."""
    allow_cross_project_access: bool = False
    llm_edit_scope: str = "markdown_only"
    max_llm_edit_size: int = 500  # lines


class ProjectMeta(BaseModel):
    """
    Schema for meta/project.yaml

    This defines what the project IS, not what's in it.
    """
    id: str = Field(..., pattern=r"^[a-z0-9-]+$", description="URL-safe project identifier")
    name: str = Field(..., min_length=1, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_opened_at: Optional[datetime] = None
    description: str = ""
    status: ProjectStatus = ProjectStatus.ACTIVE
    rules: ProjectRules = Field(default_factory=ProjectRules)


class ChatMessage(BaseModel):
    """A single message in a conversation."""
    id: str
    timestamp: datetime
    role: str = Field(..., pattern=r"^(user|assistant|system)$")
    content: str


class Conversation(BaseModel):
    """
    Schema for chat/main.json

    The single conversation thread for Phase 1.
    """
    conversation_id: str = "main"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    messages: list[ChatMessage] = Field(default_factory=list)
