from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DebtorOut
from app.services.debtors import get_debtors, parse_month

router = APIRouter(prefix="/debtors", tags=["debtors"])


@router.get("", response_model=list[DebtorOut])
def list_debtors(
    month: str | None = Query(
        default=None,
        description="YYYY-MM. Berilmasa — joriy oy (Asia/Tashkent)",
        examples=["2026-10"],
    ),
    db: Session = Depends(get_db),
) -> list[DebtorOut]:
    month_start, month_end = parse_month(month)
    return get_debtors(db, month_start, month_end)
