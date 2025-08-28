from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.subjects import Subject as SubjectModel
from schemas.subjects import SubjectCreate

router = APIRouter(prefix="/subjects", tags=["과목 정보"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ [CREATE] 과목 정보 추가
@router.post("/")
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db)):
    db_subject = SubjectModel(**subject.model_dump())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return {
        "success": True,
        "data": {
            "id": db_subject.id,
            "name": db_subject.name,
            "category": db_subject.category
        },
        "message": "과목 정보가 성공적으로 추가되었습니다"
    }


# ✅ [READ] 전체 과목 조회
@router.get("/")
def read_subjects(db: Session = Depends(get_db)):
    records = db.query(SubjectModel).all()
    return {
        "success": True,
        "data": [
            {"id": r.id, "name": r.name, "category": r.category}
            for r in records
        ],
        "message": "전체 과목 조회 완료"
    }


# ✅ [READ] 특정 과목 조회
@router.get("/{subject_id}")
def read_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(SubjectModel).filter(SubjectModel.id == subject_id).first()
    if subject is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "과목 정보를 찾을 수 없습니다"}
        }
    return {
        "success": True,
        "data": {
            "id": subject.id,
            "name": subject.name,
            "category": subject.category
        },
        "message": "과목 상세 조회 성공"
    }


# ✅ [UPDATE] 과목 정보 수정
@router.put("/{subject_id}")
def update_subject(subject_id: int, updated: SubjectCreate, db: Session = Depends(get_db)):
    subject = db.query(SubjectModel).filter(SubjectModel.id == subject_id).first()
    if subject is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "과목 정보를 찾을 수 없습니다"}
        }

    for key, value in updated.model_dump().items():
        setattr(subject, key, value)

    db.commit()
    db.refresh(subject)
    return {
        "success": True,
        "data": {
            "id": subject.id,
            "name": subject.name,
            "category": subject.category
        },
        "message": "과목 정보가 성공적으로 수정되었습니다"
    }


# ✅ [DELETE] 과목 삭제
@router.delete("/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(SubjectModel).filter(SubjectModel.id == subject_id).first()
    if subject is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "과목 정보를 찾을 수 없습니다"}
        }

    db.delete(subject)
    db.commit()
    return {
        "success": True,
        "data": {"subject_id": subject_id},
        "message": "과목 정보가 성공적으로 삭제되었습니다"
    }
