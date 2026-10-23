"""Markazlashgan xato ishlovchi.

Har qanday xato bir xil ko'rinishda qaytadi:
    {"error": {"code": "...", "message": "..."}}
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Biznes-logika xatosi: router/servis ichida raise qilinadi."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, "not_found", message)


class BadRequestError(AppError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, code, message)


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


# Pydantic'ning eng ko'p uchraydigan xato turlari uchun tushunarli matn
_VALIDATION_MESSAGES = {
    "missing": "majburiy maydon",
    "extra_forbidden": "noma'lum maydon",
    "int_type": "butun son bo'lishi kerak",
    "int_parsing": "butun son bo'lishi kerak",
    "string_type": "matn bo'lishi kerak",
    "greater_than": "0 dan katta bo'lishi kerak",
    "less_than_equal": "juda katta qiymat",
    "string_too_short": "juda qisqa",
    "string_too_long": "juda uzun",
    "json_invalid": "so'rov tanasi yaroqli JSON emas",
    "model_attributes_type": "so'rov tanasi JSON obyekt bo'lishi kerak",
    "dict_type": "so'rov tanasi JSON obyekt bo'lishi kerak",
}


def _format_validation_error(exc: RequestValidationError) -> str:
    parts = []
    for err in exc.errors():
        # loc: ("body", "amount") yoki ("query", "student_id") — birinchisi ortiqcha
        field = ".".join(str(p) for p in err.get("loc", ())[1:] if isinstance(p, str))
        err_type = err.get("type", "")
        if err_type == "value_error":
            text = str(err.get("msg", "")).removeprefix("Value error, ")
        else:
            text = _VALIDATION_MESSAGES.get(err_type, err.get("msg", "noto'g'ri qiymat"))
        parts.append(f"{field}: {text}" if field else text)
    return "; ".join(parts) or "Noto'g'ri so'rov"


_HTTP_CODES = {
    404: "not_found",
    405: "method_not_allowed",
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_error",
            _format_validation_error(exc),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODES.get(exc.status_code, "http_error")
        message = exc.detail if isinstance(exc.detail, str) else "HTTP xato"
        if exc.status_code == 404 and message == "Not Found":
            message = "Bunday manzil topilmadi"
        elif exc.status_code == 405:
            message = "Bu manzil uchun bunday HTTP metod qo'llanmaydi"
        return error_response(exc.status_code, code, message)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Kutilmagan xato: %s %s", request.method, request.url.path)
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "Serverda kutilmagan xato yuz berdi",
        )
