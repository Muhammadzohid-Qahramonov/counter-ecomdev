"""Boshlang'ich ma'lumot: 10 ta o'quvchi va oxirgi 3 oydagi to'lovlar.

Ishga tushirish (backend/ papkasidan):
    python seed.py

Diqqat: skript bazani tozalab, qaytadan to'ldiradi.
Sanalar joriy oyga (Toshkent vaqti) nisbatan hisoblanadi, shuning uchun
ilova qachon ishga tushirilmasin, joriy oyda qarzdorlar ko'rinadi.
"""

import datetime as dt

from app.database import Base, SessionLocal, engine
from app.models import Payment, Student
from app.timezone import today_tashkent


def month_start(today: dt.date, months_back: int) -> dt.date:
    """Joriy oydan `months_back` oy oldingi oyning 1-kuni."""
    total = today.year * 12 + (today.month - 1) - months_back
    return dt.date(total // 12, total % 12 + 1, 1)


def day_in(month_first: dt.date, day: int, today: dt.date) -> dt.date:
    """Oyning `day`-kuni, lekin bugundan keyin emas (kelajakdagi to'lov bo'lmasin)."""
    return min(month_first.replace(day=day), today)


# (ism, telefon, guruh, oylik summa, necha oy oldin qo'shilgan)
STUDENTS = [
    ("Aziz Karimov", "+998901234567", "Ingliz tili A1", 400_000, 2),
    ("Malika Yusupova", "+998911112233", "Ingliz tili A1", 400_000, 2),
    ("Javohir Tursunov", "+998933334455", "Ingliz tili B1", 500_000, 2),
    ("Dilnoza Rahimova", "+998945556677", "Ingliz tili B1", 500_000, 2),
    ("Sardor Aliyev", "+998977778899", "Matematika", 350_000, 2),
    ("Nilufar Qodirova", "+998901110022", "Matematika", 350_000, 2),
    ("Madina Xolmatova", "+998909990011", "Matematika", 350_000, 1),
    ("Bekzod Ismoilov", "+998935553311", "IT: Python", 600_000, 2),
    ("Shahnoza Ergasheva", "+998998887766", "IT: Python", 600_000, 2),
    ("Otabek Nazarov", "+998950001122", "IT: Python", 600_000, 0),
]

# ism -> [(necha oy oldin, kun, summa), ...]
PAYMENTS = {
    # har oy to'liq to'laydi
    "Aziz Karimov": [(2, 3, 400_000), (1, 4, 400_000), (0, 2, 400_000)],
    # joriy oyda qisman
    "Malika Yusupova": [(2, 5, 400_000), (1, 6, 400_000), (0, 5, 200_000)],
    # joriy oyda umuman to'lamagan
    "Javohir Tursunov": [(2, 10, 500_000), (1, 12, 300_000)],
    # joriy oyda ortiqcha to'lagan
    "Dilnoza Rahimova": [(2, 1, 500_000), (1, 1, 500_000), (0, 1, 600_000)],
    # bir oyda bir necha marta, jami oylikdan kam
    "Sardor Aliyev": [(2, 7, 350_000), (1, 8, 350_000), (0, 3, 100_000), (0, 15, 150_000)],
    # bir oyda bir necha marta, jami oylikka teng
    "Nilufar Qodirova": [(2, 2, 350_000), (1, 2, 200_000), (1, 20, 150_000), (0, 2, 175_000), (0, 9, 175_000)],
    # o'tgan oydan qo'shilgan, to'liq to'laydi
    "Madina Xolmatova": [(1, 15, 350_000), (0, 4, 350_000)],
    # o'tgan oyda to'lamagan, joriy oyda to'lagan
    "Bekzod Ismoilov": [(2, 9, 600_000), (0, 6, 600_000)],
    # har oy qisman
    "Shahnoza Ergasheva": [(2, 11, 300_000), (1, 11, 400_000), (0, 10, 450_000)],
    # joriy oyda qo'shilgan, hali to'lamagan: "Otabek Nazarov"
}


def seed() -> None:
    today = today_tashkent()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        by_name: dict[str, Student] = {}
        for name, phone, group, fee, joined_months_back in STUDENTS:
            student = Student(
                name=name,
                phone=phone,
                group=group,
                monthly_fee=fee,
                created_on=month_start(today, joined_months_back),
            )
            db.add(student)
            by_name[name] = student
        db.flush()  # student.id larni olish uchun

        payments_count = 0
        for name, items in PAYMENTS.items():
            for months_back, day, amount in items:
                db.add(
                    Payment(
                        student_id=by_name[name].id,
                        amount=amount,
                        date=day_in(month_start(today, months_back), day, today),
                    )
                )
                payments_count += 1

        db.commit()

    print(f"Tayyor: {len(STUDENTS)} ta o'quvchi, {payments_count} ta to'lov yozildi.")


if __name__ == "__main__":
    seed()
