"""GET /debtors uchun testlar.

Har bir test alohida in-memory SQLite bazada ishlaydi, shuning uchun
haqiqiy app.db ga tegmaydi va testlar bir-biriga ta'sir qilmaydi.
Ma'lumot to'g'ridan-to'g'ri bazaga yoziladi: shunda sanalarni aniq
belgilash mumkin (API kelajakdagi sanani qabul qilmaydi).
"""

import datetime as dt
from collections.abc import Iterator, Sequence

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Payment, Student

MONTH = "2026-03"
FEE = 500_000


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # barcha ulanishlar bitta in-memory bazani ko'radi
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def add_student(db: Session, name: str, payments: Sequence[tuple[dt.date, int]] = ()) -> Student:
    student = Student(
        name=name,
        phone="+998901234567",
        group="Ingliz tili A1",
        monthly_fee=FEE,
        created_on=dt.date(2026, 1, 1),
    )
    db.add(student)
    db.flush()
    for pay_date, amount in payments:
        db.add(Payment(student_id=student.id, amount=amount, date=pay_date))
    db.commit()
    return student


def get_debtors(client: TestClient) -> list[dict]:
    response = client.get("/debtors", params={"month": MONTH})
    assert response.status_code == 200
    return response.json()


def test_student_without_payments_is_debtor_with_full_fee(client: TestClient, db: Session) -> None:
    # Boshqa oydagi to'lov hisobga olinmasligi kerak
    student = add_student(db, "Javohir", payments=[(dt.date(2026, 2, 28), FEE)])

    debtors = get_debtors(client)

    assert debtors == [
        {
            "id": student.id,
            "name": "Javohir",
            "phone": "+998901234567",
            "group": "Ingliz tili A1",
            "monthly_fee": FEE,
            "paid": 0,
            "debt": FEE,
        }
    ]


def test_partially_paid_student_is_debtor_with_remaining_amount(
    client: TestClient, db: Session
) -> None:
    # Bir oyda ikki marta to'lov: summalar qo'shiladi (100k + 150k = 250k)
    add_student(
        db,
        "Malika",
        payments=[(dt.date(2026, 3, 1), 100_000), (dt.date(2026, 3, 31), 150_000)],
    )

    debtors = get_debtors(client)

    assert len(debtors) == 1
    assert debtors[0]["paid"] == 250_000
    assert debtors[0]["debt"] == 250_000


def test_fully_paid_student_is_not_debtor(client: TestClient, db: Session) -> None:
    add_student(db, "Aziz", payments=[(dt.date(2026, 3, 5), FEE)])

    assert get_debtors(client) == []


def test_overpaid_student_is_not_debtor_and_overpayment_does_not_carry_over(
    client: TestClient, db: Session
) -> None:
    add_student(db, "Dilnoza", payments=[(dt.date(2026, 3, 10), FEE + 300_000)])

    # Shu oyda qarzdor emas (qarz manfiy bo'lib ketmaydi)
    assert get_debtors(client) == []

    # Ortiqcha 300k keyingi oyga o'tmaydi: aprelda to'liq oylik qarz
    response = client.get("/debtors", params={"month": "2026-04"})
    assert response.status_code == 200
    assert [(d["paid"], d["debt"]) for d in response.json()] == [(0, FEE)]
