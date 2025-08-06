from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.teachers import Teacher as TeacherModel
from schemas.teachers import TeacherCreate, Teacher


router = APIRouter(prefix="/teachers", tags=["교사 정보"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 교사 정보 추가
@router.post("/", response_model=Teacher)
def create_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    db_teacher = TeacherModel(**teacher.model_dump())
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

# ✅ [READ] 전체 교사 조회
@router.get("/", response_model=list[Teacher])
def read_teachers(db: Session = Depends(get_db)):
    return db.query(TeacherModel).all()

# ✅ [READ] 특정 교사 조회
@router.get("/{teacher_id}", response_model=Teacher)
def read_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(TeacherModel).filter(TeacherModel.id == teacher_id).first()
    if teacher is None:
        raise HTTPException(status_code=404, detail="❌ 교사 정보를 찾을 수 없습니다")
    return teacher

# ✅ [UPDATE] 교사 정보 수정
@router.put("/{teacher_id}", response_model=Teacher)
def update_teacher(teacher_id: int, updated: TeacherCreate, db: Session = Depends(get_db)):
    teacher = db.query(TeacherModel).filter(TeacherModel.id == teacher_id).first()
    if teacher is None:
        raise HTTPException(status_code=404, detail="❌ 교사 정보를 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(teacher, key, value)
    db.commit()
    db.refresh(teacher)
    return teacher

# ✅ [DELETE] 교사 삭제
@router.delete("/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(TeacherModel).filter(TeacherModel.id == teacher_id).first()
    if teacher is None:
        raise HTTPException(status_code=404, detail="❌ 교사 정보를 찾을 수 없습니다")
    db.delete(teacher)
    db.commit()
    return {"message": "✅ 교사 정보가 성공적으로 삭제되었습니다"}
