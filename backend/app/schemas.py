import datetime as dt
import re
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from app.timezone import today_tashkent

# O'zbekiston raqami: +998 va 9 ta raqam (masalan +998901234567)
PHONE_RE = re.compile(r"^\+998\d{9}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

MAX_AMOUNT = 100_000_000  # 100 mln so'm — tasodifiy ortiqcha nollardan himoya

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
Group = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
# strict=True: "50000" (matn), 50000.0 yoki true kabi qiymatlar qabul qilinmaydi
Money = Annotated[int, Field(strict=True, gt=0, le=MAX_AMOUNT)]


def normalize_phone(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    cleaned = re.sub(r"[\s\-()]", "", value)
    if cleaned.startswith("998"):
        cleaned = "+" + cleaned
    if not PHONE_RE.match(cleaned):
        raise ValueError("telefon +998XXXXXXXXX formatida bo'lishi kerak")
    return cleaned


# ---------- O'quvchilar ----------


class StudentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name
    phone: str
    group: Group
    monthly_fee: Money

    _check_phone = field_validator("phone", mode="before")(normalize_phone)


class StudentUpdate(BaseModel):
    """PATCH uchun: faqat yuborilgan maydonlar o'zgaradi."""

    model_config = ConfigDict(extra="forbid")

    name: Name | None = None
    phone: str | None = None
    group: Group | None = None
    monthly_fee: Money | None = None

    _check_phone = field_validator("phone", mode="before")(normalize_phone)

    @model_validator(mode="after")
    def _no_explicit_nulls(self) -> "StudentUpdate":
        # {"name": null} — bu "o'chirish" emas, xato so'rov
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} null bo'lishi mumkin emas")
        return self


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    group: str
    monthly_fee: int
    created_on: dt.date


# ---------- To'lovlar ----------


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: Annotated[int, Field(strict=True, gt=0)]
    amount: Money
    # Berilmasa — bugungi sana (Toshkent vaqti bilan)
    date: dt.date = Field(default_factory=today_tashkent)

    @field_validator("date", mode="before")
    @classmethod
    def _iso_date_only(cls, value: Any) -> Any:
        # Pydantic standart holatda unix timestamp'ni ham sana deb qabul qiladi;
        # bizga faqat YYYY-MM-DD kerak
        if not isinstance(value, str) or not ISO_DATE_RE.match(value):
            raise ValueError("sana ISO formatda bo'lishi kerak: YYYY-MM-DD")
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            raise ValueError("bunday sana mavjud emas") from None

    @field_validator("date")
    @classmethod
    def _not_in_future(cls, value: dt.date) -> dt.date:
        if value > today_tashkent():
            raise ValueError("kelajakdagi sana bilan to'lov kiritib bo'lmaydi")
        return value


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    amount: int
    date: dt.date


# ---------- Qarzdorlar ----------


class DebtorOut(BaseModel):
    id: int
    name: str
    phone: str
    group: str
    monthly_fee: int
    paid: int  # shu oyda to'langan jami summa
    debt: int  # monthly_fee - paid
