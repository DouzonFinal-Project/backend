from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.grades import Grade as GradeModel
from schemas.grades import Grade as GradeSchema

router = APIRouter(prefix="/grades", tags=["성적 정보"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 성적 정보 추가
@router.post("/", response_model=GradeSchema)
def create_grade(grade: GradeSchema, db: Session = Depends(get_db)):
    db_grade = GradeModel(**grade.model_dump())
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade

# ✅ [READ] 전체 성적 조회
@router.get("/", response_model=list[GradeSchema])
def read_grades(db: Session = Depends(get_db)):
    return db.query(GradeModel).all()

# ✅ [READ] 특정 성적 조회
@router.get("/{grade_id}", response_model=GradeSchema)
def read_grade(grade_id: int, db: Session = Depends(get_db)):
    grade = db.query(GradeModel).filter(GradeModel.id == grade_id).first()
    if grade is None:
        raise HTTPException(status_code=404, detail="성적 정보를 찾을 수 없습니다")
    return grade

# ✅ [UPDATE] 성적 정보 수정
@router.put("/{grade_id}", response_model=GradeSchema)
def update_grade(grade_id: int, updated: GradeSchema, db: Session = Depends(get_db)):
    grade = db.query(GradeModel).filter(GradeModel.id == grade_id).first()
    if grade is None:
        raise HTTPException(status_code=404, detail="성적 정보를 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(grade, key, value)
    db.commit()
    db.refresh(grade)
    return grade

# ✅ [DELETE] 성적 삭제
@router.delete("/{grade_id}")
def delete_grade(grade_id: int, db: Session = Depends(get_db)):
    grade = db.query(GradeModel).filter(GradeModel.id == grade_id).first()
    if grade is None:
        raise HTTPException(status_code=404, detail="성적 정보를 찾을 수 없습니다")
    db.delete(grade)
    db.commit()
    return {"message": "성적 정보가 성공적으로 삭제되었습니다"}
