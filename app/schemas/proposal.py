from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.proposal import ProposalStatus

class ProposalBase(BaseModel):
    cover_letter: str
    proposed_hourly_rate: float
    estimated_hours: Optional[float] = None

class ProposalCreate(ProposalBase):
    project_id: int

class ProposalResponse(ProposalBase):
    id: int
    project_id: int
    developer_id: int
    status: ProposalStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProposalWithDeveloperInfo(ProposalResponse):
    developer_name: Optional[str] = None
    developer_email: str