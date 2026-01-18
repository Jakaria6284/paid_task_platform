from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.models.task import Task, TaskStatus
from app.models.proposal import Proposal, ProposalStatus
from app.schemas.task import TaskCreate, TaskUpdate
import logging

# Configure logging
logger = logging.getLogger(__name__)

# ==================== CREATE TASK ====================
def create_task(db: Session, task: TaskCreate):
    """
    Create a new task and assign it to a developer
    
    Schema:
    {
        "title": "string",
        "description": "string",
        "project_id": 0,
        "developer_id": 0,
        "hourly_rate": 0
    }
    """
    try:
        logger.info("=" * 50)
        logger.info("CREATE TASK - Request Data")
        logger.info("=" * 50)
        logger.info(f"Title: {task.title}")
        logger.info(f"Description: {task.description}")
        logger.info(f"Project ID: {task.project_id}")
        logger.info(f"Developer ID: {task.developer_id}")
        logger.info(f"Hourly Rate: {task.hourly_rate}")
        logger.info("=" * 50)
        
        db_task = Task(
            title=task.title,
            description=task.description,
            project_id=task.project_id,
            developer_id=task.developer_id,
            hourly_rate=task.hourly_rate,
            status=TaskStatus.TODO
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        logger.info("=" * 50)
        logger.info("TASK CREATED SUCCESSFULLY")
        logger.info("=" * 50)
        logger.info(f"Task ID: {db_task.id}")
        logger.info(f"Status: {db_task.status}")
        logger.info(f"Created At: {db_task.created_at}")
        logger.info("=" * 50 + "\n")
        
        return db_task
    except Exception as e:
        logger.error("=" * 50)
        logger.error("ERROR CREATING TASK")
        logger.error("=" * 50)
        logger.error(f"Exception: {str(e)}")
        logger.error("=" * 50 + "\n")
        db.rollback()
        raise

# ==================== ASSIGN TASK ====================
def assign_task(db: Session, project_id: int, developer_id: int, task_data: TaskCreate):
    """
    Assign a task to a developer for a specific project
    """
    try:
        logger.info("=" * 50)
        logger.info("ASSIGN TASK - Request Data")
        logger.info("=" * 50)
        logger.info(f"Project ID: {project_id}")
        logger.info(f"Developer ID: {developer_id}")
        logger.info(f"Task Title: {task_data.title}")
        logger.info(f"Task Description: {task_data.description}")
        logger.info(f"Hourly Rate: {task_data.hourly_rate}")
        logger.info("=" * 50)
        
        # Create task with project and developer
        db_task = Task(
            title=task_data.title,
            description=task_data.description,
            project_id=project_id,
            developer_id=developer_id,
            hourly_rate=task_data.hourly_rate,
            status=TaskStatus.TODO
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        logger.info("=" * 50)
        logger.info("TASK ASSIGNED SUCCESSFULLY")
        logger.info("=" * 50)
        logger.info(f"Task ID: {db_task.id}")
        logger.info(f"Project ID: {db_task.project_id}")
        logger.info(f"Developer ID: {db_task.developer_id}")
        logger.info(f"Status: {db_task.status}")
        logger.info("=" * 50 + "\n")
        
        return db_task
    except Exception as e:
        logger.error("=" * 50)
        logger.error("ERROR ASSIGNING TASK")
        logger.error("=" * 50)
        logger.error(f"Exception: {str(e)}")
        logger.error("=" * 50 + "\n")
        db.rollback()
        raise

# ==================== ACCEPT PROPOSAL AND CREATE TASK ====================
def accept_proposal_and_create_task(db: Session, proposal_id: int):
    """
    When buyer accepts a proposal:
    1. Update proposal status to accepted
    2. Create and assign task to the developer
    3. Update project is_open to False (mark as assigned)
    4. Return task details
    """
    try:
        logger.info("=" * 50)
        logger.info("ACCEPT PROPOSAL & CREATE TASK")
        logger.info("=" * 50)
        logger.info(f"Proposal ID: {proposal_id}")
        logger.info("=" * 50)
        
        # Get the proposal
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            logger.error("=" * 50)
            logger.error("PROPOSAL NOT FOUND")
            logger.error("=" * 50 + "\n")
            return None
        
        logger.info("PROPOSAL DETAILS")
        logger.info("=" * 50)
        logger.info(f"Proposal ID: {proposal.id}")
        logger.info(f"Project ID: {proposal.project_id}")
        logger.info(f"Developer ID: {proposal.developer_id}")
        logger.info(f"Proposed Rate: ${proposal.proposed_hourly_rate}/hr")
        logger.info(f"Estimated Hours: {proposal.estimated_hours}")
        logger.info(f"Status: {proposal.status}")
        logger.info("=" * 50)
        
        # Update proposal status to accepted
        proposal.status = ProposalStatus.ACCEPTED
        proposal.accepted_at = datetime.utcnow()
        db.commit()
        
        logger.info("PROPOSAL UPDATED")
        logger.info("=" * 50)
        logger.info(f"New Status: {proposal.status}")
        logger.info(f"Accepted At: {proposal.accepted_at}")
        logger.info("=" * 50)
        
        # ==================== UPDATE PROJECT IS_OPEN ====================
        logger.info("=" * 50)
        logger.info("UPDATING PROJECT STATUS")
        logger.info("=" * 50)
        logger.info(f"Project ID: {proposal.project_id}")
        logger.info(f"Setting is_open: True -> False")
        
        project = proposal.project
        if project:
            project.is_open = False
            db.commit()
            logger.info(f"Project Updated - is_open: {project.is_open}")
            logger.info("Project moved from 'Awaiting Developer' to 'Running'")
        else:
            logger.warning(f"Project not found for ID: {proposal.project_id}")
        
        logger.info("=" * 50)
        
        # Create task from proposal
        logger.info("=" * 50)
        logger.info("CREATING TASK FROM PROPOSAL")
        logger.info("=" * 50)
        
        db_task = Task(
            title=proposal.project.title,  # Use project title
            description=proposal.project.description,  # Use project description
            project_id=proposal.project_id,
            developer_id=proposal.developer_id,
            hourly_rate=proposal.proposed_hourly_rate  # Use proposed rate
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        logger.info("TASK CREATED SUCCESSFULLY")
        logger.info("=" * 50)
        logger.info(f"Task ID: {db_task.id}")
        logger.info(f"Project ID: {db_task.project_id}")
        logger.info(f"Developer ID: {db_task.developer_id}")
        logger.info(f"Hourly Rate: ${db_task.hourly_rate}/hr")
        logger.info(f"Status: {db_task.status}")
        logger.info("=" * 50 + "\n")
        
        return {
            "proposal": proposal,
            "task": db_task,
            "project": project
        }
    except Exception as e:
        logger.error("=" * 50)
        logger.error("ERROR ACCEPTING PROPOSAL & CREATING TASK")
        logger.error("=" * 50)
        logger.error(f"Exception: {str(e)}")
        logger.error("=" * 50 + "\n")
        db.rollback()
        raise

# ==================== GET TASK ====================
def get_task(db: Session, task_id: int):
    """Get a specific task by ID"""
    logger.info(f"Fetching Task ID: {task_id}")
    return db.query(Task).filter(Task.id == task_id).first()

# ==================== GET TASKS BY PROJECT ====================
def get_tasks_by_project(db: Session, project_id: int):
    """Get all tasks for a project"""
    logger.info(f"Fetching tasks for Project ID: {project_id}")
    return db.query(Task).filter(Task.project_id == project_id).all()

# ==================== GET TASKS BY DEVELOPER ====================
def get_tasks_by_developer(db: Session, developer_id: int):
    """Get all tasks assigned to a developer"""
    logger.info(f"Fetching tasks for Developer ID: {developer_id}")
    return db.query(Task).filter(Task.developer_id == developer_id).all()

# ==================== GET ALL TASKS ====================
def get_all_tasks(db: Session, skip: int = 0, limit: int = 100):
    """Get all tasks with pagination"""
    logger.info(f"Fetching all tasks - Skip: {skip}, Limit: {limit}")
    return db.query(Task).offset(skip).limit(limit).all()

# ==================== UPDATE TASK ====================
def update_task(db: Session, task_id: int, task_update: TaskUpdate):
    """Update task details"""
    try:
        logger.info("=" * 50)
        logger.info("UPDATE TASK")
        logger.info("=" * 50)
        logger.info(f"Task ID: {task_id}")
        logger.info(f"Update Data: {task_update.model_dump(exclude_unset=True)}")
        logger.info("=" * 50)
        
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if db_task:
            update_data = task_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_task, key, value)
            db.commit()
            db.refresh(db_task)
            
            logger.info("TASK UPDATED SUCCESSFULLY")
            logger.info(f"New Status: {db_task.status}")
            logger.info("=" * 50 + "\n")
        
        return db_task
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}")
        db.rollback()
        raise

# ==================== SUBMIT TASK ====================
def submit_task(db: Session, task_id: int, time_spent: float, file_path: str):
    """Submit a task with time spent and solution file"""
    try:
        logger.info("=" * 50)
        logger.info("SUBMIT TASK")
        logger.info("=" * 50)
        logger.info(f"Task ID: {task_id}")
        logger.info(f"Time Spent: {time_spent} hours")
        logger.info(f"File Path: {file_path}")
        logger.info("=" * 50)
        
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if db_task:
            db_task.time_spent = time_spent
            db_task.solution_file_path = file_path
            db_task.status = TaskStatus.SUBMITTED
            db_task.submitted_at = datetime.utcnow()
            db.commit()
            db.refresh(db_task)
            
            logger.info("TASK SUBMITTED SUCCESSFULLY")
            logger.info(f"New Status: {db_task.status}")
            logger.info(f"Submitted At: {db_task.submitted_at}")
            logger.info("=" * 50 + "\n")
        
        return db_task
    except Exception as e:
        logger.error(f"Error submitting task: {str(e)}")
        db.rollback()
        raise

# ==================== MARK TASK AS PAID ====================
def mark_task_as_paid(db: Session, task_id: int):
    """Mark a task as paid"""
    try:
        logger.info("=" * 50)
        logger.info("MARK TASK AS PAID")
        logger.info("=" * 50)
        logger.info(f"Task ID: {task_id}")
        logger.info("=" * 50)
        
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if db_task:
            db_task.status = TaskStatus.PAID
            db.commit()
            db.refresh(db_task)
            
            logger.info("TASK MARKED AS PAID")
            logger.info(f"New Status: {db_task.status}")
            logger.info("=" * 50 + "\n")
        
        return db_task
    except Exception as e:
        logger.error(f"Error marking task as paid: {str(e)}")
        db.rollback()
        raise

# ==================== COUNT ALL TASKS ====================
def count_all_tasks(db: Session):
    """Get total count of tasks"""
    count = db.query(Task).count()
    logger.info(f"Total Tasks Count: {count}")
    return count

# ==================== COUNT TASKS BY STATUS ====================
def count_tasks_by_status(db: Session, status: TaskStatus):
    """Count tasks by status"""
    count = db.query(Task).filter(Task.status == status).count()
    logger.info(f"Tasks Count with status {status}: {count}")
    return count

# ==================== GET TOTAL HOURS LOGGED ====================
def get_total_hours_logged(db: Session):
    """Get total hours spent on all tasks"""
    result = db.query(func.sum(Task.time_spent)).scalar()
    total = result if result else 0.0
    logger.info(f"Total Hours Logged: {total}")
    return total