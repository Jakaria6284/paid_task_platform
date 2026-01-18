from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.task import TaskStatus

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None

class TaskCreate(TaskBase):
    project_id: int
    developer_id: int
    hourly_rate: float

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    time_spent: Optional[float] = None

class TaskSubmission(BaseModel):
    time_spent: float

class TaskResponse(TaskBase):
    id: int
    project_id: int
    developer_id: int
    hourly_rate: float
    status: TaskStatus
    time_spent: float
    solution_file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True