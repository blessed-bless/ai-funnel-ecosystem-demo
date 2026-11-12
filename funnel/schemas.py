from datetime import datetime

from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    source: str = Field(default="landing", max_length=64)
    name: str = Field(default="", max_length=120)
    contact: str = Field(default="", max_length=120)
    interest: str = Field(default="", max_length=240)
    summary: str = Field(default="")
    telegram_user_id: str = Field(default="", max_length=64)


class LeadOut(BaseModel):
    id: int
    source: str
    name: str
    contact: str
    interest: str
    summary: str
    status: str
    telegram_user_id: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class LeadStatusUpdate(BaseModel):
    status: str = Field(pattern=r"^(new|qualified|won|lost|spam)$")


class ChatRequest(BaseModel):
    session_key: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=4000)
    source: str = Field(default="web_chat", max_length=64)


class ChatResponse(BaseModel):
    reply: str
    draft_lead: LeadCreate | None = None
    ready_to_submit: bool = False


class FunnelStats(BaseModel):
    leads_total: int
    leads_new: int
    leads_qualified: int
    by_source: dict[str, int]
