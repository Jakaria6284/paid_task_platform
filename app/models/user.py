from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    BUYER = "buyer"
    DEVELOPER = "developer"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="buyer", foreign_keys="Project.buyer_id")
    assigned_tasks = relationship("Task", back_populates="developer", foreign_keys="Task.developer_id")
    payments = relationship("Payment", back_populates="buyer", foreign_keys="Payment.buyer_id")