from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.classes import Class as ClassModel
from schemas.classes import Class as ClassSchema

router = APIRouter(prefix="/classes", tags=["학급 정보"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 학급 정보 추가
@router.post("/", response_model=ClassSchema)
def create_class(class_: ClassSchema, db: Session = Depends(get_db)):
    db_class = ClassModel(**class_.model_dump())
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

# ✅ [READ] 전체 학급 조회
@router.get("/", response_model=list[ClassSchema])
def read_classes(db: Session = Depends(get_db)):
    return db.query(ClassModel).all()

# ✅ [READ] 특정 학급 조회
@router.get("/{class_id}", response_model=ClassSchema)
def read_class(class_id: int, db: Session = Depends(get_db)):
    class_ = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if class_ is None:
        raise HTTPException(status_code=404, detail="학급 정보를 찾을 수 없습니다")
    return class_

# ✅ [UPDATE] 학급 정보 수정
@router.put("/{class_id}", response_model=ClassSchema)
def update_class(class_id: int, updated: ClassSchema, db: Session = Depends(get_db)):
    class_ = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if class_ is None:
        raise HTTPException(status_code=404, detail="학급 정보를 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(class_, key, value)
    db.commit()
    db.refresh(class_)
    return class_

# ✅ [DELETE] 학급 삭제
@router.delete("/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    class_ = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if class_ is None:
        raise HTTPException(status_code=404, detail="학급 정보를 찾을 수 없습니다")
    db.delete(class_)
    db.commit()
    return {"message": "학급 정보가 성공적으로 삭제되었습니다"}
