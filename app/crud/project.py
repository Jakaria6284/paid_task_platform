from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

def create_project(db: Session, project: ProjectCreate, buyer_id: int):
    db_project = Project(
        title=project.title,
        description=project.description,
        buyer_id=buyer_id,
        expected_hourly_rate=project.expected_hourly_rate,
        expected_duration_hours=project.expected_duration_hours,
        tags=project.tags or []
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def get_project(db: Session, project_id: int):
    return db.query(Project).filter(Project.id == project_id).first()

def get_projects_by_buyer(db: Session, buyer_id: int, skip: int = 0, limit: int = 100):
    return db.query(Project).filter(Project.buyer_id == buyer_id).offset(skip).limit(limit).all()

def get_all_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Project).offset(skip).limit(limit).all()

def get_open_projects(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    tags: Optional[List[str]] = None,
    min_rate: Optional[float] = None,
    max_rate: Optional[float] = None,
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None
):
    """
    Get open projects with optional filters for developers to browse
    """
    query = db.query(Project).filter(Project.is_open == True)
    
    # Search in title and description
    if search:
        search_filter = or_(
            Project.title.ilike(f"%{search}%"),
            Project.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Filter by tags (any match)
    if tags and len(tags) > 0:
        # Check if any of the provided tags exist in project tags
        tag_filters = [Project.tags.contains([tag]) for tag in tags]
        query = query.filter(or_(*tag_filters))
    
    # Filter by hourly rate range
    if min_rate is not None:
        query = query.filter(Project.expected_hourly_rate >= min_rate)
    if max_rate is not None:
        query = query.filter(Project.expected_hourly_rate <= max_rate)
    
    # Filter by duration range
    if min_duration is not None:
        query = query.filter(Project.expected_duration_hours >= min_duration)
    if max_duration is not None:
        query = query.filter(Project.expected_duration_hours <= max_duration)
    
    return query.offset(skip).limit(limit).all()

def update_project(db: Session, project_id: int, project_update: ProjectUpdate):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project:
        update_data = project_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_project, key, value)
        db.commit()
        db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: int):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project:
        db.delete(db_project)
        db.commit()
        return True
    return False

def count_all_projects(db: Session):
    return db.query(Project).count()