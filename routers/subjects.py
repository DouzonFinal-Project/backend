from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.subjects import Subject as SubjectModel
from schemas.subjects import Subject as SubjectSchema, SubjectCreate  # ✅ 입력/출력 스키마 모두 import

router = APIRouter(prefix="/subjects", tags=["과목 정보"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 과목 정보 추가
@router.post("/", response_model=SubjectSchema)
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db)):
    db_subject = SubjectModel(**subject.model_dump())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

# ✅ [READ] 전체 과목 조회
@router.get("/", response_model=list[SubjectSchema])
def read_subjects(db: Session = Depends(get_db)):
    return db.query(SubjectModel).all()

# ✅ [READ] 특정 과목 조회
@router.get("/{subject_id}", response_model=SubjectSchema)
def read_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(SubjectModel).filter(SubjectModel.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=404, detail="과목 정보를 찾을 수 없습니다")
    return subject

# ✅ [UPDATE] 과목 정보 수정
@router.put("/{subject_id}", response_model=SubjectSchema)
def update_subject(subject_id: int, updated: SubjectCreate, db: Session = Depends(get_db)):
    subject = db.query(SubjectModel).filter(SubjectModel.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=404, detail="과목 정보를 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(subject, key, value)
    db.commit()
    db.refresh(subject)
    return subject

# ✅ [DELETE] 과목 삭제
@router.delete("/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(SubjectModel).filter(SubjectModel.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=404, detail="과목 정보를 찾을 수 없습니다")
    db.delete(subject)
    db.commit()
    return {"message": "과목 정보가 성공적으로 삭제되었습니다"}
