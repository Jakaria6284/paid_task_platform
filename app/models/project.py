from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, Float, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # NEW: Buyer's expectations
    expected_hourly_rate = Column(Float, nullable=False)  # Buyer's budget per hour
    expected_duration_hours = Column(Float, nullable=False)  # How many hours buyer expects
    
    # NEW: Tags for searchability
    tags = Column(ARRAY(String), default=[])  # e.g., ["flutter", "ai", "backend"]
    
    is_open = Column(Boolean, default=True)  # Open for proposals or closed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    buyer = relationship("User", back_populates="projects", foreign_keys=[buyer_id])
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="project", cascade="all, delete-orphan")