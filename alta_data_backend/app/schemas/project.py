from pydantic import BaseModel, Field, EmailStr


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ''


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    created_by_id: str


class InvitationCreate(BaseModel):
    email: EmailStr
    role: str  # admin | contributor | reviewer


class InvitationAccept(BaseModel):
    token: str


class SubmitForReviewRequest(BaseModel):
    documentId: str


