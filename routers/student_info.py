from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.student_info import StudentInfo as StudentInfoModel
from schemas.student_info import StudentInfo as StudentInfoSchema
from database.db import SessionLocal

router = APIRouter(prefix="/student-info", tags=["학생 인적사항"])

# ✅ 데이터베이스 세션 종속성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 학생 등록
@router.post("/", response_model=StudentInfoSchema)
def create_student(student: StudentInfoSchema, db: Session = Depends(get_db)):
    """
    새로운 학생 정보를 등록합니다.
    """
    db_student = StudentInfoModel(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# ✅ [READ] 전체 학생 조회
@router.get("/", response_model=list[StudentInfoSchema])
def read_students(db: Session = Depends(get_db)):
    """
    등록된 전체 학생 목록을 조회합니다.
    """
    return db.query(StudentInfoModel).all()

# ✅ [READ] 특정 학생 조회
@router.get("/{student_id}", response_model=StudentInfoSchema)
def read_student(student_id: int, db: Session = Depends(get_db)):
    """
    특정 student_id에 해당하는 학생 정보를 조회합니다.
    """
    student = db.query(StudentInfoModel).filter(StudentInfoModel.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")
    return student

# ✅ [UPDATE] 학생 정보 수정
@router.put("/{student_id}", response_model=StudentInfoSchema)
def update_student(student_id: int, updated: StudentInfoSchema, db: Session = Depends(get_db)):
    """
    student_id에 해당하는 학생 정보를 수정합니다.
    """
    student = db.query(StudentInfoModel).filter(StudentInfoModel.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")
    for key, value in updated.dict().items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    return student

# ✅ [DELETE] 학생 삭제
@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """
    student_id에 해당하는 학생 정보를 삭제합니다.
    """
    student = db.query(StudentInfoModel).filter(StudentInfoModel.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")
    db.delete(student)
    db.commit()
    return {"message": "학생 정보가 삭제되었습니다."}
