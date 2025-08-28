from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.teachers import Teacher as TeacherModel
from schemas.teachers import TeacherCreate

router = APIRouter(prefix="/teachers", tags=["교사 정보"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================
# [1단계] CRUD 라우터
# ==========================================================

# ✅ [CREATE] 교사 정보 추가
@router.post("/")
def create_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    db_teacher = TeacherModel(**teacher.model_dump())
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return {
        "success": True,
        "data": {
            "id": db_teacher.id,
            "name": db_teacher.name,
            "email": db_teacher.email,
            "phone": db_teacher.phone,
            "subject": db_teacher.subject,
            "role": db_teacher.role,
            "is_homeroom": db_teacher.is_homeroom,
            "homeroom_class": db_teacher.homeroom_class,
            "class_id": db_teacher.class_id
        },
        "message": "교사 정보가 성공적으로 추가되었습니다"
    }


# ✅ [READ] 전체 교사 조회
@router.get("/")
def read_teachers(db: Session = Depends(get_db)):
    records = db.query(TeacherModel).all()
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "name": r.name,
                "email": r.email,
                "phone": r.phone,
                "subject": r.subject,
                "role": r.role,
                "is_homeroom": r.is_homeroom,
                "homeroom_class": r.homeroom_class,
                "class_id": r.class_id
            }
            for r in records
        ],
        "message": "전체 교사 정보 조회 완료"
    }


# ✅ [READ] 특정 교사 조회
@router.get("/{teacher_id}")
def read_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(TeacherModel).filter(TeacherModel.id == teacher_id).first()
    if teacher is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "교사 정보를 찾을 수 없습니다"}
        }
    return {
        "success": True,
        "data": {
            "id": teacher.id,
            "name": teacher.name,
            "email": teacher.email,
            "phone": teacher.phone,
            "subject": teacher.subject,
            "role": teacher.role,
            "is_homeroom": teacher.is_homeroom,
            "homeroom_class": teacher.homeroom_class,
            "class_id": teacher.class_id
        },
        "message": "교사 상세 정보 조회 성공"
    }


# ✅ [UPDATE] 교사 정보 수정
@router.put("/{teacher_id}")
def update_teacher(teacher_id: int, updated: TeacherCreate, db: Session = Depends(get_db)):
    teacher = db.query(TeacherModel).filter(TeacherModel.id == teacher_id).first()
    if teacher is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "교사 정보를 찾을 수 없습니다"}
        }

    for key, value in updated.model_dump().items():
        setattr(teacher, key, value)

    db.commit()
    db.refresh(teacher)
    return {
        "success": True,
        "data": {
            "id": teacher.id,
            "name": teacher.name,
            "email": teacher.email,
            "phone": teacher.phone,
            "subject": teacher.subject,
            "role": teacher.role,
            "is_homeroom": teacher.is_homeroom,
            "homeroom_class": teacher.homeroom_class,
            "class_id": teacher.class_id
        },
        "message": "교사 정보가 성공적으로 수정되었습니다"
    }


# ✅ [DELETE] 교사 삭제
@router.delete("/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(TeacherModel).filter(TeacherModel.id == teacher_id).first()
    if teacher is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "교사 정보를 찾을 수 없습니다"}
        }

    db.delete(teacher)
    db.commit()
    return {
        "success": True,
        "data": {"teacher_id": teacher_id},
        "message": "교사 정보가 성공적으로 삭제되었습니다"
    }
