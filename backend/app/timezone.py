"""Vaqt zonasi bilan ishlash.

Barcha "bugun" va "joriy oy" tushunchalari Toshkent vaqti (UTC+5) bo'yicha
hisoblanadi. O'zbekistonda yozgi vaqtga o'tish yo'q, shuning uchun
tzdata paketiga bog'lanmaslik uchun qat'iy +5 soat siljishdan foydalanamiz.
"""

from datetime import date, datetime, timedelta, timezone

TASHKENT_TZ = timezone(timedelta(hours=5), name="Asia/Tashkent")


def now_tashkent() -> datetime:
    return datetime.now(TASHKENT_TZ)


def today_tashkent() -> date:
    return now_tashkent().date()
