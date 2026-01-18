from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    expected_hourly_rate: float
    expected_duration_hours: float
    tags: Optional[List[str]] = []

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    expected_hourly_rate: Optional[float] = None
    expected_duration_hours: Optional[float] = None
    tags: Optional[List[str]] = None

class ProjectResponse(ProjectBase):
    id: int
    buyer_id: int
    is_open: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProjectSearchFilters(BaseModel):
    search: Optional[str] = None  # Search in title/description
    tags: Optional[List[str]] = None  # Filter by tags
    min_rate: Optional[float] = None
    max_rate: Optional[float] = None
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None