from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import BadRequestError, NotFoundError
from app.models import Student
from app.schemas import StudentCreate, StudentOut, StudentUpdate

router = APIRouter(prefix="/students", tags=["students"])


def get_student_or_404(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise NotFoundError(f"ID={student_id} bo'lgan o'quvchi topilmadi")
    return student


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)) -> Student:
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("", response_model=list[StudentOut])
def list_students(
    group: str | None = Query(default=None, description="Guruh nomi bo'yicha aniq filtr"),
    db: Session = Depends(get_db),
) -> list[Student]:
    query = select(Student).order_by(Student.name, Student.id)
    if group is not None and group.strip():
        query = query.where(Student.group == group.strip())
    return list(db.scalars(query))


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)) -> Student:
    return get_student_or_404(db, student_id)


@router.patch("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int, payload: StudentUpdate, db: Session = Depends(get_db)
) -> Student:
    student = get_student_or_404(db, student_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise BadRequestError("empty_update", "O'zgartirish uchun kamida bitta maydon yuboring")
    for field, value in changes.items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db)) -> Response:
    student = get_student_or_404(db, student_id)
    # O'quvchining to'lovlari ham birga o'chadi (ON DELETE CASCADE)
    db.delete(student)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
