"""Qarzdorlarni hisoblash logikasi.

Qoidalar:
- Oy Toshkent vaqti bo'yicha kalendar oyi: [1-kun, keyingi oyning 1-kuni).
- O'quvchining shu oydagi barcha to'lovlari qo'shiladi.
- qarz = oylik summa - to'langan; qarz > 0 bo'lsa, o'quvchi qarzdor.
- Umuman to'lamagan o'quvchi ham qarzdor (to'langan = 0).
- Ortiqcha to'lov qarzni 0 qiladi, lekin keyingi oyga o'tkazilmaydi.
- O'quvchi qo'shilgan oydan oldingi oylar uchun qarzdor hisoblanmaydi.
"""

import datetime as dt
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import BadRequestError
from app.models import Payment, Student
from app.schemas import DebtorOut
from app.timezone import today_tashkent

MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def month_bounds(year: int, month: int) -> tuple[dt.date, dt.date]:
    """Oyning birinchi kuni va keyingi oyning birinchi kuni (oxiri kirmaydi)."""
    start = dt.date(year, month, 1)
    end = dt.date(year + 1, 1, 1) if month == 12 else dt.date(year, month + 1, 1)
    return start, end


def parse_month(value: str | None) -> tuple[dt.date, dt.date]:
    """'YYYY-MM' ni oy chegaralariga aylantiradi; berilmasa — joriy oy (Toshkent)."""
    if value is None or not value.strip():
        today = today_tashkent()
        return month_bounds(today.year, today.month)

    match = MONTH_RE.match(value.strip())
    if match is None or int(match.group(1)) < 1:
        raise BadRequestError(
            "invalid_month",
            "month parametri YYYY-MM formatida bo'lishi kerak, masalan 2026-10",
        )
    return month_bounds(int(match.group(1)), int(match.group(2)))


def calculate_debt(monthly_fee: int, paid: int) -> int:
    """Qarz hech qachon manfiy bo'lmaydi: ortiqcha to'lov qarzni 0 qiladi."""
    return max(monthly_fee - paid, 0)


def get_debtors(db: Session, month_start: dt.date, month_end: dt.date) -> list[DebtorOut]:
    # 1) Har bir o'quvchi shu oyda jami qancha to'laganini hisoblaymiz
    paid_per_student = (
        select(Payment.student_id, func.sum(Payment.amount).label("paid"))
        .where(Payment.date >= month_start, Payment.date < month_end)
        .group_by(Payment.student_id)
        .subquery()
    )

    # 2) Barcha o'quvchilarni LEFT JOIN qilamiz: to'lamaganlar ham tushib qolmasin
    rows = db.execute(
        select(Student, func.coalesce(paid_per_student.c.paid, 0))
        .outerjoin(paid_per_student, paid_per_student.c.student_id == Student.id)
        # shu oy tugashidan oldin qo'shilgan o'quvchilargina to'lashi kerak
        .where(Student.created_on < month_end)
    ).all()

    # 3) Qarzi borlarini ajratamiz
    debtors = []
    for student, paid in rows:
        debt = calculate_debt(student.monthly_fee, paid)
        if debt > 0:
            debtors.append(
                DebtorOut(
                    id=student.id,
                    name=student.name,
                    phone=student.phone,
                    group=student.group,
                    monthly_fee=student.monthly_fee,
                    paid=paid,
                    debt=debt,
                )
            )

    # Eng katta qarz tepada
    debtors.sort(key=lambda d: (-d.debt, d.name))
    return debtors
