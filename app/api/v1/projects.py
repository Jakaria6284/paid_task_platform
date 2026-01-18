from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.schemas.task import TaskResponse
from app.crud import project as project_crud
from app.crud import task as task_crud
from app.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.project import Project

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="""
    Create a new project to organize and manage tasks.
    
    **Authorization:** Buyer only
    
    **Use Case:**
    Buyers create projects to group related tasks together. Each project can contain
    multiple tasks assigned to different developers.
    
    **NEW: Proposal System**
    When you create a project, it's automatically open for developer proposals.
    Developers can submit bids, and you can review and accept the best proposal.
    
    **Request Body:**
    - title: Project name (required)
    - description: Project details (required)
    - expected_hourly_rate: Your budget per hour (required, e.g., 50.0)
    - expected_duration_hours: How many hours you expect (required, e.g., 40)
    - tags: Keywords for searchability (optional, e.g., ["flutter", "ai", "backend"])
    
    **Returns:**
    - Complete project object with:
        - id: Unique project identifier
        - title: Project name
        - description: Project details
        - buyer_id: ID of the buyer who created it
        - expected_hourly_rate: Budget per hour
        - expected_duration_hours: Expected time to complete
        - tags: Search keywords
        - is_open: true (accepting proposals)
        - created_at: Creation timestamp
        - updated_at: Last update timestamp
    
    **Example:**
    ```json
    {
      "title": "E-commerce Mobile App",
      "description": "Need a Flutter developer to build iOS/Android shopping app",
      "expected_hourly_rate": 50.0,
      "expected_duration_hours": 80,
      "tags": ["flutter", "mobile", "ecommerce", "firebase"]
    }
    ```
    
    **Next Steps After Creating:**
    1. Wait for developers to submit proposals
    2. Review proposals via GET /proposals/project/{project_id}
    3. Accept the best proposal
    4. Create and assign tasks to the selected developer
    """,
    responses={
        201: {"description": "Project created successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Only buyers can create projects"}
    }
)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.BUYER]))
):
    """Create a new project (Buyer only)"""
    return project_crud.create_project(db=db, project=project, buyer_id=current_user.id)

@router.get(
    "/",
    response_model=List[ProjectResponse],
    summary="Get all projects",
    description="""
    Retrieve list of projects based on user role.
    
    **Authorization:** Buyer, Developer, or Admin
    
    **Behavior by Role:**
    - **Buyer:** Returns only projects they created (with proposal status)
    - **Admin:** Returns all projects in the system
    - **Developer:** Returns all OPEN projects accepting proposals (with filters)
    
    **Query Parameters (For Developers):**
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return (default: 100)
    - search: Search in title/description (e.g., "ecommerce")
    - tags: Filter by tags (comma-separated, e.g., "flutter,ai")
    - min_rate: Minimum hourly rate
    - max_rate: Maximum hourly rate
    - min_duration: Minimum expected hours
    - max_duration: Maximum expected hours
    
    **Returns:**
    - Array of project objects
    - Includes is_open field showing if accepting proposals
    - Shows expected_hourly_rate and expected_duration_hours
    - Shows tags for easy filtering
    
    **Use Cases:**
    - Buyer viewing their project portfolio
    - Developer browsing projects to bid on (with filters!)
    - Admin monitoring all projects on the platform
    
    **Developer Example:**
    ```
    GET /projects?search=flutter&tags=mobile,ai&min_rate=40&max_rate=60
    ```
    This returns all open Flutter projects with mobile/AI tags, budget $40-60/hr
    """,
    responses={
        200: {"description": "List of projects returned"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied for this role"}
    }
)
def get_projects(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search in title/description"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    min_rate: Optional[float] = Query(None, description="Minimum hourly rate"),
    max_rate: Optional[float] = Query(None, description="Maximum hourly rate"),
    min_duration: Optional[float] = Query(None, description="Minimum expected hours"),
    max_duration: Optional[float] = Query(None, description="Maximum expected hours"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all projects for current user"""
    if current_user.role == UserRole.BUYER:
        return project_crud.get_projects_by_buyer(db, buyer_id=current_user.id, skip=skip, limit=limit)
    elif current_user.role == UserRole.ADMIN:
        return project_crud.get_all_projects(db, skip=skip, limit=limit)
    elif current_user.role == UserRole.DEVELOPER:
        # Developers see all open projects with filters
        tag_list = tags.split(",") if tags else None
        return project_crud.get_open_projects(
            db, 
            skip=skip, 
            limit=limit,
            search=search,
            tags=tag_list,
            min_rate=min_rate,
            max_rate=max_rate,
            min_duration=min_duration,
            max_duration=max_duration
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
    description="""
    Retrieve detailed information about a specific project.
    
    **Authorization:** Buyer (owner only) or Admin
    
    **Path Parameters:**
    - project_id: Unique identifier of the project
    
    **Access Control:**
    - Buyers can only view their own projects
    - Admins can view any project
    
    **Returns:**
    - Complete project object with all details
    
    **Use Case:**
    View project details before managing tasks or checking progress
    """,
    responses={
        200: {"description": "Project details returned"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied - not your project"},
        404: {"description": "Project not found"}
    }
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific project"""
    project = project_crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Authorization check
    if current_user.role == UserRole.BUYER and project.buyer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return project

@router.get(
    "/{project_id}/tasks",
    response_model=List[TaskResponse],
    summary="Get all tasks in a project",
    description="""
    Retrieve all tasks associated with a specific project.
    
    **Authorization:** Buyer (owner only) or Admin
    
    **Path Parameters:**
    - project_id: Unique identifier of the project
    
    **Returns:**
    - Array of task objects including:
        - Task details (title, description)
        - Assigned developer
        - Hourly rate
        - Status (todo, in_progress, submitted, paid)
        - Time spent
        - Solution file path (if submitted)
        - Timestamps
    
    **Use Cases:**
    - Buyer checking progress of all tasks in their project
    - Admin monitoring task completion rates
    - Viewing which tasks are pending payment
    """,
    responses={
        200: {"description": "List of tasks returned"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied - not your project"},
        404: {"description": "Project not found"}
    }
)
def get_project_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.BUYER, UserRole.ADMIN]))
):
    """Get all tasks for a project"""
    project = project_crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Authorization check
    if current_user.role == UserRole.BUYER and project.buyer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return task_crud.get_tasks_by_project(db, project_id=project_id)

@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="""
    Update project title and/or description.
    
    **Authorization:** Buyer (owner only)
    
    **Path Parameters:**
    - project_id: Unique identifier of the project
    
    **Request Body (all optional):**
    - title: New project name
    - description: New project description
    
    **Note:** You can update one or both fields. Only send the fields you want to change.
    
    **Returns:**
    - Updated project object
    
    **Use Case:**
    Update project details as requirements evolve or to fix typos
    """,
    responses={
        200: {"description": "Project updated successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied - not your project"},
        404: {"description": "Project not found"}
    }
)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.BUYER]))
):
    """Update a project (Buyer only)"""
    project = project_crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    if project.buyer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return project_crud.update_project(db, project_id=project_id, project_update=project_update)

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="""
    Permanently delete a project and all associated tasks.
    
    **Authorization:** Buyer (owner only)
    
    **Path Parameters:**
    - project_id: Unique identifier of the project
    
    **⚠️ Warning:**
    - This action is irreversible
    - All tasks under this project will be deleted (CASCADE)
    - Associated payments will remain in the database for records
    
    **Returns:**
    - 204 No Content on success
    
    **Use Case:**
    Remove cancelled or completed projects from the system
    """,
    responses={
        204: {"description": "Project deleted successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied - not your project"},
        404: {"description": "Project not found"}
    }
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.BUYER]))
):
    """Delete a project (Buyer only)"""
    project = project_crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    if project.buyer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    project_crud.delete_project(db, project_id=project_id)