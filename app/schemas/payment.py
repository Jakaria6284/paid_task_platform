from pydantic import BaseModel
from datetime import datetime

class PaymentCreate(BaseModel):
    task_id: int

class PaymentResponse(BaseModel):
    id: int
    task_id: int
    buyer_id: int
    amount: float
    created_at: datetime
    
    class Config:
        from_attributes = True