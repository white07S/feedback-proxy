# schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Literal, List
import config

TypeLiteral = Literal[tuple(config.FEEDBACK_TYPES)]
StatusLiteral = Literal[tuple(config.STATUSES)]
SeverityLiteral = Literal[tuple(config.SEVERITIES)]

class ProjectOut(BaseModel):
    key: str
    name: str
    active: bool

class FeedbackCreate(BaseModel):
    project_key: str = Field(..., examples=["nfrfscenario"])
    type: TypeLiteral
    title: str
    description: str
    severity: Optional[SeverityLiteral] = None
    created_by: str  # from frontend hard-coded user

class FeedbackUpdate(BaseModel):
    status: Optional[StatusLiteral] = None
    assignee: Optional[str] = None
    resolution: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[SeverityLiteral] = None

class FeedbackOut(BaseModel):
    id: int
    project_key: str
    type: str
    title: str
    description: str
    severity: Optional[str]
    status: str
    created_by: str
    assignee: Optional[str]
    resolution: Optional[str]
    created_at: str
    updated_at: str

class CommentCreate(BaseModel):
    body: str
    created_by: str

class CommentOut(BaseModel):
    id: int
    feedback_id: int
    body: str
    created_by: str
    created_at: str

class FeedbackListOut(BaseModel):
    items: List[FeedbackOut]
    total: int
    page: int
    page_size: int