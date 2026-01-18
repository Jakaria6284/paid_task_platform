from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.proposal import ProposalCreate, ProposalResponse, ProposalWithDeveloperInfo
from app.crud import proposal as proposal_crud
from app.crud import project as project_crud
from app.crud import user as user_crud
from app.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.proposal import ProposalStatus

router = APIRouter(prefix="/proposals", tags=["Proposals"])

@router.post(
    "/",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a proposal to a project",
    description="Developer submits a proposal (bid) to work on a project"
)
def submit_proposal(
    proposal: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.DEVELOPER]))
):
    """Submit a proposal to a project (Developer only)"""
    project = project_crud.get_project(db, project_id=proposal.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    if not project.is_open:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is closed for proposals"
        )
    
    existing = proposal_crud.check_existing_proposal(db, proposal.project_id, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted a proposal for this project"
        )
    
    return proposal_crud.create_proposal(db=db, proposal=proposal, developer_id=current_user.id)

@router.get(
    "/my-proposals",
    response_model=List[ProposalResponse],
    summary="Get my submitted proposals"
)
def get_my_proposals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.DEVELOPER]))
):
    """Get all proposals submitted by current developer"""
    return proposal_crud.get_proposals_by_developer(db, developer_id=current_user.id)

@router.get(
    "/project/{project_id}",
    response_model=List[ProposalWithDeveloperInfo],
    summary="Get all proposals for a project"
)
def get_project_proposals(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all proposals for a project (Buyer or Admin only)"""
    project = project_crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    if current_user.role == UserRole.BUYER and project.buyer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    proposals = proposal_crud.get_proposals_by_project(db, project_id=project_id)
    
    result = []
    for prop in proposals:
        developer = user_crud.get_user_by_id(db, prop.developer_id)
        proposal_dict = {
            "id": prop.id,
            "project_id": prop.project_id,
            "developer_id": prop.developer_id,
            "cover_letter": prop.cover_letter,
            "proposed_hourly_rate": prop.proposed_hourly_rate,
            "estimated_hours": prop.estimated_hours,
            "status": prop.status,
            "created_at": prop.created_at,
            "updated_at": prop.updated_at,
            "developer_name": developer.full_name,
            "developer_email": developer.email
        }
        result.append(ProposalWithDeveloperInfo(**proposal_dict))
    
    return result

@router.post(
    "/{proposal_id}/accept",
    response_model=ProposalResponse,
    summary="Accept a proposal and hire developer"
)
def accept_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.BUYER]))
):
    """Accept a proposal (Buyer only)"""
    proposal = proposal_crud.get_proposal(db, proposal_id=proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    
    project = project_crud.get_project(db, project_id=proposal.project_id)
    if project.buyer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    accepted = proposal_crud.accept_proposal(db, proposal_id=proposal_id)
    project.is_open = False
    db.commit()
    
    return accepted

@router.post(
    "/{proposal_id}/reject",
    response_model=ProposalResponse,
    summary="Reject a proposal"
)
def reject_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.BUYER]))
):
    """Reject a proposal (Buyer only)"""
    proposal = proposal_crud.get_proposal(db, proposal_id=proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    
    project = project_crud.get_project(db, project_id=proposal.project_id)
    if project.buyer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return proposal_crud.reject_proposal(db, proposal_id=proposal_id)