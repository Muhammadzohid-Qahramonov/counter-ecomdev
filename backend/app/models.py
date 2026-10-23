import datetime as dt

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.timezone import today_tashkent


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    group: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Pul butun so'mda saqlanadi: float'dagi yaxlitlash xatolari bo'lmaydi
    monthly_fee: Mapped[int] = mapped_column(Integer, nullable=False)
    # Qaysi oydan boshlab to'lov talab qilinishini bilish uchun (Toshkent sanasi)
    created_on: Mapped[dt.date] = mapped_column(Date, nullable=False, default=today_tashkent)

    payments: Mapped[list["Payment"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    # To'lov sanasi Toshkent vaqti bo'yicha kalendar kuni (vaqtsiz)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)

    student: Mapped[Student] = relationship(back_populates="payments")
