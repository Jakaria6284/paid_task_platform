from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class ProposalStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class Proposal(Base):
    __tablename__ = "proposals"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    developer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cover_letter = Column(Text, nullable=False)  # Developer's proposal message
    proposed_hourly_rate = Column(Float, nullable=False)  # Developer's rate
    estimated_hours = Column(Float)  # How long developer thinks it will take
    status = Column(Enum(ProposalStatus), default=ProposalStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="proposals")
    developer = relationship("User", back_populates="proposals", foreign_keys=[developer_id])