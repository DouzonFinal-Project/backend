from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.grades import Grade as GradeModel
from schemas.grades import Grade as GradeSchema, GradeCreate
from database.db import SessionLocal

router = APIRouter(prefix="/grades", tags=["성적 관리"])

# ✅ DB 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 성적 등록
@router.post("/", response_model=GradeSchema)
def create_grade(grade: GradeCreate, db: Session = Depends(get_db)):
    """
    새로운 성적 정보를 등록합니다.
    """
    db_grade = GradeModel(**grade.dict())
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade

# ✅ [READ] 전체 성적 조회
@router.get("/", response_model=list[GradeSchema])
def read_all_grades(db: Session = Depends(get_db)):
    """
    전체 성적 정보를 조회합니다.
    """
    return db.query(GradeModel).all()

# ✅ [READ] 특정 학생의 성적 조회
@router.get("/student/{student_id}", response_model=list[GradeSchema])
def read_grades_by_student(student_id: int, db: Session = Depends(get_db)):
    """
    특정 학생(student_id)의 성적 정보를 조회합니다.
    """
    records = db.query(GradeModel).filter(GradeModel.student_id == student_id).all()
    if not records:
        raise HTTPException(status_code=404, detail="성적 정보가 없습니다.")
    return records

# ✅ [DELETE] 성적 정보 삭제
@router.delete("/{grade_id}")
def delete_grade(grade_id: int, db: Session = Depends(get_db)):
    """
    특정 성적 정보를 삭제합니다.
    """
    record = db.query(GradeModel).filter(GradeModel.grade_id == grade_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="성적 정보를 찾을 수 없습니다.")
    db.delete(record)
    db.commit()
    return {"message": "성적 정보가 삭제되었습니다."}
