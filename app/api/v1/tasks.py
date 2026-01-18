from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskSubmission
from app.crud import task as task_crud
from app.crud import project as project_crud
from app.crud import user as user_crud
from app.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.task import TaskStatus
from app.utils.file import save_task_file
import os

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.crud import task as task_crud
from app.models.user import User
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])

# ==================== CREATE TASK ====================
@router.post("/create", response_model=TaskResponse)
def create_new_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new task (Buyer creates task)
    
    Schema:
    {
        "title": "string",
        "description": "string",
        "project_id": 0,
        "developer_id": 0,
        "hourly_rate": 0
    }
    """
    logger.info("=" * 60)
    logger.info("CREATE TASK ENDPOINT - Request Received")
    logger.info("=" * 60)
    logger.info(f"Current User: {current_user.id} ({current_user.email})")
    logger.info(f"Request Body:")
    logger.info(json.dumps({
        "title": task_data.title,
        "description": task_data.description,
        "project_id": task_data.project_id,
        "developer_id": task_data.developer_id,
        "hourly_rate": task_data.hourly_rate
    }, indent=2))
    logger.info("=" * 60)
    
    try:
        task = task_crud.create_task(db, task_data)
        
        logger.info("=" * 60)
        logger.info("TASK CREATED - Response")
        logger.info("=" * 60)
        logger.info(json.dumps({
            "id": task.id,
            "title": task.title,
            "project_id": task.project_id,
            "developer_id": task.developer_id,
            "status": str(task.status),
            "hourly_rate": task.hourly_rate
        }, indent=2))
        logger.info("=" * 60 + "\n")
        
        return task
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"ERROR CREATING TASK: {str(e)}")
        logger.error("=" * 60 + "\n")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== ASSIGN TASK ====================
@router.post("/assign", response_model=TaskResponse)
def assign_task_to_developer(
    project_id: int,
    developer_id: int,
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assign a task to a developer
    """
    logger.info("=" * 60)
    logger.info("ASSIGN TASK ENDPOINT - Request Received")
    logger.info("=" * 60)
    logger.info(f"Current User: {current_user.id} ({current_user.email})")
    logger.info(f"Parameters:")
    logger.info(f"  Project ID: {project_id}")
    logger.info(f"  Developer ID: {developer_id}")
    logger.info(f"Request Body:")
    logger.info(json.dumps({
        "title": task_data.title,
        "description": task_data.description,
        "hourly_rate": task_data.hourly_rate
    }, indent=2))
    logger.info("=" * 60)
    
    try:
        task = task_crud.assign_task(db, project_id, developer_id, task_data)
        
        logger.info("=" * 60)
        logger.info("TASK ASSIGNED - Response")
        logger.info("=" * 60)
        logger.info(json.dumps({
            "id": task.id,
            "title": task.title,
            "project_id": task.project_id,
            "developer_id": task.developer_id,
            "status": str(task.status),
            "hourly_rate": task.hourly_rate
        }, indent=2))
        logger.info("=" * 60 + "\n")
        
        return task
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"ERROR ASSIGNING TASK: {str(e)}")
        logger.error("=" * 60 + "\n")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== GET TASK ====================
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific task by ID"""
    logger.info(f"GET TASK ENDPOINT - Task ID: {task_id}")
    
    task = task_crud.get_task(db, task_id)
    if not task:
        logger.error(f"Task not found - ID: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    
    logger.info(f"Task found: {task.id} - {task.title}")
    return task

# ==================== GET MY TASKS (Developer) ====================
@router.get("/", response_model=list[TaskResponse])
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tasks assigned to the current developer"""
    logger.info("=" * 60)
    logger.info("GET MY TASKS ENDPOINT - Request Received")
    logger.info("=" * 60)
    logger.info(f"Developer ID: {current_user.id}")
    logger.info(f"Developer Email: {current_user.email}")
    logger.info("=" * 60)
    
    tasks = task_crud.get_tasks_by_developer(db, current_user.id)
    
    logger.info("=" * 60)
    logger.info("TASKS RETRIEVED - Response")
    logger.info("=" * 60)
    logger.info(f"Total Tasks: {len(tasks)}")
    for task in tasks:
        logger.info(f"  - Task ID: {task.id}, Title: {task.title}, Status: {task.status}")
    logger.info("=" * 60 + "\n")
    
    return tasks

# ==================== GET PROJECT TASKS ====================
@router.get("/project/{project_id}", response_model=list[TaskResponse])
def get_project_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tasks for a specific project"""
    logger.info(f"GET PROJECT TASKS ENDPOINT - Project ID: {project_id}")
    
    tasks = task_crud.get_tasks_by_project(db, project_id)
    logger.info(f"Found {len(tasks)} tasks for project {project_id}")
    
    return tasks

# ==================== UPDATE TASK ====================
@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update task details"""
    logger.info("=" * 60)
    logger.info("UPDATE TASK ENDPOINT - Request Received")
    logger.info("=" * 60)
    logger.info(f"Task ID: {task_id}")
    logger.info(f"Update Data: {task_update.model_dump(exclude_unset=True)}")
    logger.info("=" * 60)
    
    task = task_crud.update_task(db, task_id, task_update)
    
    if not task:
        logger.error(f"Task not found for update - ID: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    
    logger.info("=" * 60)
    logger.info("TASK UPDATED - Response")
    logger.info("=" * 60)
    logger.info(f"Task ID: {task.id}")
    logger.info(f"New Status: {task.status}")
    logger.info("=" * 60 + "\n")
    
    return task

# ==================== SUBMIT TASK ====================
@router.post("/{task_id}/submit")
def submit_task(
    task_id: int,
    time_spent: float = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a completed task with time spent and solution file"""
    logger.info("=" * 60)
    logger.info("SUBMIT TASK ENDPOINT - Request Received")
    logger.info("=" * 60)
    logger.info(f"Task ID: {task_id}")
    logger.info(f"Developer ID: {current_user.id}")
    logger.info(f"Time Spent: {time_spent} hours")
    logger.info(f"File Name: {file.filename}")
    logger.info("=" * 60)
    
    # Save file and get path (implement based on your storage solution)
    file_path = f"/uploads/{task_id}/{file.filename}"
    
    try:
        task = task_crud.submit_task(db, task_id, time_spent, file_path)
        
        if not task:
            logger.error(f"Task not found - ID: {task_id}")
            raise HTTPException(status_code=404, detail="Task not found")
        
        logger.info("=" * 60)
        logger.info("TASK SUBMITTED - Response")
        logger.info("=" * 60)
        logger.info(f"Task ID: {task.id}")
        logger.info(f"Status: {task.status}")
        logger.info(f"Submitted At: {task.submitted_at}")
        logger.info("=" * 60 + "\n")
        
        return {
            "message": "Task submitted successfully",
            "task_id": task.id,
            "status": str(task.status)
        }
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"ERROR SUBMITTING TASK: {str(e)}")
        logger.error("=" * 60 + "\n")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== ACCEPT PROPOSAL & CREATE TASK ====================
@router.post("/proposal/{proposal_id}/accept-and-create-task")
def accept_proposal_and_create_task(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    When buyer accepts a proposal:
    1. Update proposal status to accepted
    2. Create and assign task to the developer
    3. Return both proposal and task details
    """
    logger.info("=" * 60)
    logger.info("ACCEPT PROPOSAL & CREATE TASK ENDPOINT")
    logger.info("=" * 60)
    logger.info(f"Proposal ID: {proposal_id}")
    logger.info(f"Buyer ID: {current_user.id}")
    logger.info("=" * 60)
    
    try:
        result = task_crud.accept_proposal_and_create_task(db, proposal_id)
        
        if not result:
            logger.error(f"Proposal not found - ID: {proposal_id}")
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        proposal = result["proposal"]
        task = result["task"]
        
        logger.info("=" * 60)
        logger.info("PROPOSAL ACCEPTED & TASK CREATED - Response")
        logger.info("=" * 60)
        logger.info("Proposal Details:")
        logger.info(json.dumps({
            "proposal_id": proposal.id,
            "status": str(proposal.status),
            "accepted_at": str(proposal.accepted_at)
        }, indent=2))
        logger.info("Task Details:")
        logger.info(json.dumps({
            "task_id": task.id,
            "title": task.title,
            "project_id": task.project_id,
            "developer_id": task.developer_id,
            "hourly_rate": task.hourly_rate,
            "status": str(task.status)
        }, indent=2))
        logger.info("=" * 60 + "\n")
        
        return {
            "message": "Proposal accepted and task created successfully",
            "proposal": {
                "id": proposal.id,
                "status": str(proposal.status),
                "accepted_at": proposal.accepted_at
            },
            "task": {
                "id": task.id,
                "title": task.title,
                "project_id": task.project_id,
                "developer_id": task.developer_id,
                "hourly_rate": task.hourly_rate,
                "status": str(task.status)
            }
        }
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"ERROR ACCEPTING PROPOSAL & CREATING TASK: {str(e)}")
        logger.error("=" * 60 + "\n")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{task_id}/download")
def download_task_file(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download task solution file (only after payment)
    
    Returns:
        FileResponse: The ZIP file with task solution
    """
    logger.info("=" * 60)
    logger.info("DOWNLOAD TASK FILE ENDPOINT - Request Received")
    logger.info("=" * 60)
    logger.info(f"Task ID: {task_id}")
    logger.info(f"User ID: {current_user.id}")
    logger.info("=" * 60)
    
    try:
        # Get task
        task = task_crud.get_task(db, task_id)
        if not task:
            logger.error(f"Task not found - ID: {task_id}")
            raise HTTPException(status_code=404, detail="Task not found")
        
        logger.info(f"Task Found: {task.title}")
        logger.info(f"Task Status: {task.status}")
        logger.info(f"Task Status Value: {task.status.value if hasattr(task.status, 'value') else task.status}")
        
        # Check if task is paid
        # Compare with enum value, not string
        is_paid = (
            str(task.status).lower() == 'taskstatus.paid' or 
            str(task.status).lower() == 'paid' or
            (hasattr(task.status, 'value') and task.status.value == 'paid')
        )
        
        if not is_paid:
            logger.error(f"Task not paid - ID: {task_id}, Status: {task.status}")
            raise HTTPException(
                status_code=403,
                detail=f"Task must be paid before downloading. Current status: {task.status}"
            )
        
        # Check if file exists
        file_path = task.solution_file_path
        if not file_path:
            logger.error(f"File path is empty - Task ID: {task_id}")
            raise HTTPException(status_code=404, detail="Solution file path not set")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found at path - Path: {file_path}")
            raise HTTPException(status_code=404, detail="Solution file not found on server")
        
        logger.info(f"File Path: {file_path}")
        logger.info(f"File Size: {os.path.getsize(file_path)} bytes")
        logger.info(f"File Exists: True")
        logger.info("=" * 60 + "\n")
        
        # Return file for download
        return FileResponse(
            path=file_path,
            filename=f"task_{task_id}_solution.zip",
            media_type='application/zip'
        )
    
    except HTTPException as he:
        logger.error("=" * 60)
        logger.error(f"HTTP Exception: {he.detail}")
        logger.error("=" * 60 + "\n")
        raise he
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"ERROR DOWNLOADING FILE: {str(e)}")
        logger.error("=" * 60 + "\n")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== MARK TASK AS PAID ====================
@router.post("/{task_id}/mark-paid")
def mark_task_as_paid(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a task as paid"""
    logger.info("=" * 60)
    logger.info("MARK TASK AS PAID ENDPOINT - Request Received")
    logger.info("=" * 60)
    logger.info(f"Task ID: {task_id}")
    logger.info("=" * 60)
    
    try:
        task = task_crud.mark_task_as_paid(db, task_id)
        
        if not task:
            logger.error(f"Task not found - ID: {task_id}")
            raise HTTPException(status_code=404, detail="Task not found")
        
        logger.info("=" * 60)
        logger.info("TASK MARKED AS PAID - Response")
        logger.info("=" * 60)
        logger.info(f"Task ID: {task.id}")
        logger.info(f"Status: {task.status}")
        logger.info("=" * 60 + "\n")
        
        return {
            "message": "Task marked as paid",
            "task_id": task.id,
            "status": str(task.status)
        }
    except Exception as e:
        logger.error(f"ERROR MARKING TASK AS PAID: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))