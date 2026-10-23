from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Payment
from app.routers.students import get_student_or_404
from app.schemas import PaymentCreate, PaymentOut

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)) -> Payment:
    # Mavjud bo'lmagan o'quvchiga to'lov yozilmaydi — 404
    get_student_or_404(db, payload.student_id)
    payment = Payment(**payload.model_dump())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.get("", response_model=list[PaymentOut])
def list_payments(
    student_id: int | None = Query(default=None, gt=0, description="O'quvchi ID si"),
    db: Session = Depends(get_db),
) -> list[Payment]:
    query = select(Payment).order_by(Payment.date.desc(), Payment.id.desc())
    if student_id is not None:
        get_student_or_404(db, student_id)
        query = query.where(Payment.student_id == student_id)
    return list(db.scalars(query))
