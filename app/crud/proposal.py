from sqlalchemy.orm import Session
from app.models.proposal import Proposal, ProposalStatus
from app.schemas.proposal import ProposalCreate

def create_proposal(db: Session, proposal: ProposalCreate, developer_id: int):
    db_proposal = Proposal(
        project_id=proposal.project_id,
        developer_id=developer_id,
        cover_letter=proposal.cover_letter,
        proposed_hourly_rate=proposal.proposed_hourly_rate,
        estimated_hours=proposal.estimated_hours,
        status=ProposalStatus.PENDING
    )
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    return db_proposal

def get_proposal(db: Session, proposal_id: int):
    return db.query(Proposal).filter(Proposal.id == proposal_id).first()

def get_proposals_by_project(db: Session, project_id: int):
    return db.query(Proposal).filter(Proposal.project_id == project_id).all()

def get_proposals_by_developer(db: Session, developer_id: int):
    return db.query(Proposal).filter(Proposal.developer_id == developer_id).all()

def check_existing_proposal(db: Session, project_id: int, developer_id: int):
    return db.query(Proposal).filter(
        Proposal.project_id == project_id,
        Proposal.developer_id == developer_id
    ).first()

def accept_proposal(db: Session, proposal_id: int):
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if proposal:
        # Accept this proposal
        proposal.status = ProposalStatus.ACCEPTED
        
        # Reject all other proposals for the same project
        db.query(Proposal).filter(
            Proposal.project_id == proposal.project_id,
            Proposal.id != proposal_id,
            Proposal.status == ProposalStatus.PENDING
        ).update({"status": ProposalStatus.REJECTED})
        
        db.commit()
        db.refresh(proposal)
    return proposal

def reject_proposal(db: Session, proposal_id: int):
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if proposal:
        proposal.status = ProposalStatus.REJECTED
        db.commit()
        db.refresh(proposal)
    return proposal

def get_accepted_proposal_for_project(db: Session, project_id: int):
    return db.query(Proposal).filter(
        Proposal.project_id == project_id,
        Proposal.status == ProposalStatus.ACCEPTED
    ).first()