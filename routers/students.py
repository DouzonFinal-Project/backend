from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.students import Student as StudentModel
from schemas.students import Student as StudentSchema

router = APIRouter(prefix="/students", tags=["학생 정보"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 학생 정보 추가
@router.post("/", response_model=StudentSchema)
def create_student(student: StudentSchema, db: Session = Depends(get_db)):
    db_student = StudentModel(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# ✅ [READ] 전체 학생 조회
@router.get("/", response_model=list[StudentSchema])
def read_students(db: Session = Depends(get_db)):
    return db.query(StudentModel).all()

# ✅ [READ] 특정 학생 조회
@router.get("/{student_id}", response_model=StudentSchema)
def read_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="학생 정보를 찾을 수 없습니다")
    return student

# ✅ [UPDATE] 학생 정보 수정
@router.put("/{student_id}", response_model=StudentSchema)
def update_student(student_id: int, updated: StudentSchema, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="학생 정보를 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    return student

# ✅ [DELETE] 학생 삭제
@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="학생 정보를 찾을 수 없습니다")
    db.delete(student)
    db.commit()
    return {"message": "학생 정보가 성공적으로 삭제되었습니다"}
