from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.crud import payment as payment_crud
from app.crud import task as task_crud
from app.crud import project as project_crud
from app.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.task import TaskStatus

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Make payment for submitted task",
    description="""
    Process payment for a submitted task to unlock the solution.
    
    **Authorization:** Buyer (project owner only)
    
    **Request Body:**
    - task_id: ID of the task to pay for (required)
    
    **Payment Workflow:**
    1. Developer submits task with time spent (e.g., 8.5 hours)
    2. Buyer sees task status "submitted" but **cannot download** solution
    3. Buyer calls this endpoint to make payment
    4. System calculates: amount = hourly_rate × time_spent
    5. Payment record is created
    6. Task status changes from "submitted" to "paid"
    7. **Solution is now unlocked** for download
    
    **Automatic Calculations:**
    - Amount is calculated automatically from task data
    - No need to send amount in request
    - Formula: hourly_rate × time_spent
    
    **Example:**
    - Task hourly rate: $50/hour
    - Developer spent: 6.5 hours
    - Automatic payment: $325.00
    
    **Validations:**
    - Task must exist and belong to your project
    - Task status must be "submitted" (not "todo", "in_progress", or already "paid")
    - Cannot pay for same task twice
    
    **Returns:**
    - Payment record with:
        - id: Payment identifier
        - task_id: Associated task
        - buyer_id: Your user ID
        - amount: Total amount paid
        - created_at: Payment timestamp
    
    **After Payment:**
    - Task status → "paid"
    - Can now download solution via GET /tasks/{task_id}/download
    - Payment is final and cannot be reversed (in this system)
    """,
    responses={
        201: {"description": "Payment processed successfully"},
        400: {"description": "Task not submitted or already paid"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied - not your project"},
        404: {"description": "Task not found"}
    }
)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.BUYER]))
):
    """Make payment for a submitted task (Buyer only)"""
    # Get task
    task = task_crud.get_task(db, task_id=payment.task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    # Verify buyer owns the project
    project = project_crud.get_project(db, project_id=task.project_id)
    if project.buyer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Verify task is submitted
    if task.status != TaskStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task must be submitted before payment"
        )
    
    # Check if payment already exists
    existing_payment = payment_crud.get_payment_by_task(db, task_id=payment.task_id)
    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already made for this task"
        )
    
    # Calculate amount
    amount = task.hourly_rate * task.time_spent
    
    # Create payment
    db_payment = payment_crud.create_payment(
        db=db,
        payment=payment,
        buyer_id=current_user.id,
        amount=amount
    )
    
    # Mark task as paid
    task_crud.mark_task_as_paid(db, task_id=payment.task_id)
    
    return db_payment

@router.get(
    "/my-payments",
    response_model=List[PaymentResponse],
    summary="Get payment history",
    description="""
    Retrieve all payments made by the current buyer.
    
    **Authorization:** Buyer only
    
    **Returns:**
    - Array of all payments you've made
    - Each payment includes:
        - Payment ID
        - Task ID that was paid for
        - Amount paid
        - Payment timestamp
    
    **Use Cases:**
    - View payment history
    - Track total spending on tasks
    - Verify which tasks have been paid
    - Generate financial reports
    - Check payment dates for accounting
    
    **Sorting:**
    - Returns payments ordered by creation date (newest first)
    
    **Financial Summary:**
    - Use this to calculate total expenses
    - Cross-reference with task completion rates
    - Verify all submitted tasks are paid
    """,
    responses={
        200: {"description": "List of payments returned"},
        401: {"description": "Not authenticated"},
        403: {"description": "Only buyers can access payment history"}
    }
)
def get_my_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.BUYER]))
):
    """Get all payments made by current buyer"""
    return payment_crud.get_payments_by_buyer(db, buyer_id=current_user.id)

@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Get payment details",
    description="""
    Retrieve detailed information about a specific payment.
    
    **Authorization:** Buyer (who made payment), Developer (who earned it), or Admin
    
    **Path Parameters:**
    - payment_id: Unique identifier of the payment
    
    **Access Control:**
    - Buyers can only view their own payments
    - Developers can view payments for tasks assigned to them
    - Admins can view any payment
    
    **Returns:**
    - Complete payment record:
        - id: Payment identifier
        - task_id: Which task was paid
        - buyer_id: Who made the payment
        - amount: Payment amount
        - created_at: When payment was made
    
    **Use Cases:**
    - Verify payment details
    - Check payment amount
    - Confirm payment date
    - Resolve disputes
    - Generate receipts/invoices
    
    **Additional Info:**
    - Can cross-reference task_id to get task details
    - Amount reflects hourly_rate × time_spent at time of payment
    """,
    responses={
        200: {"description": "Payment details returned"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied - not your payment"},
        404: {"description": "Payment not found"}
    }
)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific payment"""
    payment = payment_crud.get_payment(db, payment_id=payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    # Authorization check
    if current_user.role == UserRole.BUYER and payment.buyer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif current_user.role == UserRole.DEVELOPER:
        task = task_crud.get_task(db, task_id=payment.task_id)
        if task.developer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return payment