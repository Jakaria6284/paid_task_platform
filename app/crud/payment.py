from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate

def create_payment(db: Session, payment: PaymentCreate, buyer_id: int, amount: float):
    db_payment = Payment(
        task_id=payment.task_id,
        buyer_id=buyer_id,
        amount=amount
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_payment(db: Session, payment_id: int):
    return db.query(Payment).filter(Payment.id == payment_id).first()

def get_payment_by_task(db: Session, task_id: int):
    return db.query(Payment).filter(Payment.task_id == task_id).first()

def get_payments_by_buyer(db: Session, buyer_id: int):
    return db.query(Payment).filter(Payment.buyer_id == buyer_id).all()

def get_all_payments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Payment).offset(skip).limit(limit).all()

def count_all_payments(db: Session):
    return db.query(Payment).count()

def get_total_revenue(db: Session):
    result = db.query(func.sum(Payment.amount)).scalar()
    return result if result else 0.0