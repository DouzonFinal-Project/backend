from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.test_scores import TestScore as TestScoreModel
from schemas.test_scores import TestScore as TestScoreSchema

router = APIRouter(prefix="/test_scores", tags=["시험성적"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================
# [1단계] CRUD 라우터
# ==========================================================

# ✅ [CREATE] 시험 성적 추가
@router.post("/")
def create_test_score(score: TestScoreSchema, db: Session = Depends(get_db)):
    db_score = TestScoreModel(**score.model_dump())
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    return {
        "success": True,
        "data": {
            "id": db_score.id,
            "test_id": db_score.test_id,
            "student_id": db_score.student_id,
            "score": db_score.score,
            "subject_name": db_score.subject_name
        },
        "message": "시험 성적이 성공적으로 추가되었습니다"
    }


# ✅ [READ] 전체 성적 조회
@router.get("/")
def read_test_scores(db: Session = Depends(get_db)):
    records = db.query(TestScoreModel).all()
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "test_id": r.test_id,
                "student_id": r.student_id,
                "score": r.score,
                "subject_name": r.subject_name
            }
            for r in records
        ],
        "message": "전체 시험 성적 조회 완료"
    }


# ✅ [READ] 성적 상세 조회
@router.get("/{score_id}")
def read_test_score(score_id: int, db: Session = Depends(get_db)):
    score = db.query(TestScoreModel).filter(TestScoreModel.id == score_id).first()
    if score is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "시험 성적을 찾을 수 없습니다"}
        }
    return {
        "success": True,
        "data": {
            "id": score.id,
            "test_id": score.test_id,
            "student_id": score.student_id,
            "score": score.score,
            "subject_name": score.subject_name
        },
        "message": "시험 성적 상세 조회 성공"
    }


# ✅ [UPDATE] 성적 수정
@router.put("/{score_id}")
def update_test_score(score_id: int, updated: TestScoreSchema, db: Session = Depends(get_db)):
    score = db.query(TestScoreModel).filter(TestScoreModel.id == score_id).first()
    if score is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "시험 성적을 찾을 수 없습니다"}
        }

    for key, value in updated.model_dump().items():
        setattr(score, key, value)

    db.commit()
    db.refresh(score)
    return {
        "success": True,
        "data": {
            "id": score.id,
            "test_id": score.test_id,
            "student_id": score.student_id,
            "score": score.score,
            "subject_name": score.subject_name
        },
        "message": "시험 성적이 성공적으로 수정되었습니다"
    }


# ✅ [DELETE] 성적 삭제
@router.delete("/{score_id}")
def delete_test_score(score_id: int, db: Session = Depends(get_db)):
    score = db.query(TestScoreModel).filter(TestScoreModel.id == score_id).first()
    if score is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "시험 성적을 찾을 수 없습니다"}
        }

    db.delete(score)
    db.commit()
    return {
        "success": True,
        "data": {"score_id": score_id},
        "message": "시험 성적이 성공적으로 삭제되었습니다"
    }
