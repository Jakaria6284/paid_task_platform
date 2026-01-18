from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict
from app.database import get_db
from app.crud import user as user_crud
from app.crud import project as project_crud
from app.crud import task as task_crud
from app.crud import payment as payment_crud
from app.dependencies import require_role
from app.models.user import User, UserRole
from app.models.task import TaskStatus

router = APIRouter(prefix="/admin", tags=["Admin"])

class DashboardStats(BaseModel):
    total_buyers: int
    total_developers: int
    total_projects: int
    total_tasks: int
    tasks_todo: int
    tasks_in_progress: int
    tasks_submitted: int
    tasks_completed: int
    total_payments: int
    pending_payments: int
    total_developer_hours: float
    total_revenue: float

@router.get(
    "/dashboard",
    response_model=DashboardStats,
    summary="Get admin dashboard statistics",
    description="""
    Retrieve comprehensive platform statistics for monitoring and analysis.
    
    **Authorization:** Admin only
    
    **Returns Complete Platform Overview:**
    
    **User Statistics:**
    - total_buyers: Number of registered buyers
    - total_developers: Number of registered developers
    
    **Project Statistics:**
    - total_projects: All projects created on platform
    
    **Task Statistics:**
    - total_tasks: All tasks ever created
    - tasks_todo: Tasks not yet started
    - tasks_in_progress: Tasks currently being worked on
    - tasks_submitted: Tasks submitted but awaiting payment
    - tasks_completed: Tasks fully paid (revenue generated)
    
    **Payment Statistics:**
    - total_payments: Number of completed payments
    - pending_payments: Submitted tasks awaiting payment (potential revenue)
    
    **Financial Metrics:**
    - total_developer_hours: Sum of all time logged across all tasks
    - total_revenue: Sum of all payments made (actual earnings)
    
    **Use Cases:**
    - Monitor platform growth
    - Track revenue generation
    - Identify bottlenecks (too many pending payments?)
    - Analyze developer productivity (hours logged)
    - Generate executive reports
    - Monitor task completion rates
    - Calculate average hourly rates
    - Track payment velocity
    
    **Calculations You Can Do:**
    - Average payment: total_revenue / total_payments
    - Average hourly rate: total_revenue / total_developer_hours
    - Payment conversion rate: tasks_completed / tasks_submitted
    - Task completion rate: tasks_completed / total_tasks
    - Pending revenue: (tasks_submitted × average_rate)
    
    **Example Response:**
    ```json
    {
      "total_buyers": 45,
      "total_developers": 120,
      "total_projects": 156,
      "total_tasks": 523,
      "tasks_todo": 87,
      "tasks_in_progress": 145,
      "tasks_submitted": 48,
      "tasks_completed": 243,
      "total_payments": 243,
      "pending_payments": 48,
      "total_developer_hours": 1846.5,
      "total_revenue": 92325.00
    }
    ```
    
    **Admin Dashboard Features:**
    - Read-only access (admins cannot modify data)
    - Real-time statistics
    - No pagination (single comprehensive view)
    - All amounts in base currency units
    """,
    responses={
        200: {"description": "Dashboard statistics returned"},
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"}
    }
)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Get admin dashboard statistics"""
    
    # User counts
    total_buyers = user_crud.count_users_by_role(db, UserRole.BUYER)
    total_developers = user_crud.count_users_by_role(db, UserRole.DEVELOPER)
    
    # Project counts
    total_projects = project_crud.count_all_projects(db)
    
    # Task counts
    total_tasks = task_crud.count_all_tasks(db)
    tasks_todo = task_crud.count_tasks_by_status(db, TaskStatus.TODO)
    tasks_in_progress = task_crud.count_tasks_by_status(db, TaskStatus.IN_PROGRESS)
    tasks_submitted = task_crud.count_tasks_by_status(db, TaskStatus.SUBMITTED)
    tasks_completed = task_crud.count_tasks_by_status(db, TaskStatus.PAID)
    
    # Payment counts
    total_payments = payment_crud.count_all_payments(db)
    pending_payments = tasks_submitted  # Submitted but not paid
    
    # Hours and revenue
    total_developer_hours = task_crud.get_total_hours_logged(db)
    total_revenue = payment_crud.get_total_revenue(db)
    
    return DashboardStats(
        total_buyers=total_buyers,
        total_developers=total_developers,
        total_projects=total_projects,
        total_tasks=total_tasks,
        tasks_todo=tasks_todo,
        tasks_in_progress=tasks_in_progress,
        tasks_submitted=tasks_submitted,
        tasks_completed=tasks_completed,
        total_payments=total_payments,
        pending_payments=pending_payments,
        total_developer_hours=total_developer_hours,
        total_revenue=total_revenue
    )