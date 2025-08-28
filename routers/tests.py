from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.db import SessionLocal
from models.tests import Test as TestModel
from models.test_scores import TestScore as TestScoreModel
from models.students import Student as StudentModel
from schemas.tests import TestCreate

router = APIRouter(prefix="/tests", tags=["시험 관리"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================
# [1단계] CRUD 기본 라우터
# ==========================================================

# ✅ [CREATE] 시험 추가
@router.post("/")
def create_test(new_test: TestCreate, db: Session = Depends(get_db)):
    db_test = TestModel(**new_test.model_dump())
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return {
        "success": True,
        "data": {
            "id": db_test.id,
            "subject_id": db_test.subject_id,
            "test_name": db_test.test_name,
            "test_date": str(db_test.test_date),
            "class_id": db_test.class_id,
            "subject_name": db_test.subject_name
        },
        "message": "시험이 성공적으로 추가되었습니다"
    }


# ✅ [READ] 전체 시험 목록
@router.get("/")
def read_tests(db: Session = Depends(get_db)):
    records = db.query(TestModel).all()
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "subject_id": r.subject_id,
                "test_name": r.test_name,
                "test_date": str(r.test_date),
                "class_id": r.class_id,
                "subject_name": r.subject_name
            }
            for r in records
        ],
        "message": "전체 시험 목록 조회 완료"
    }


# ==========================================================
# [2단계] 정적 라우터
# ==========================================================

# ✅ [READ] 특정 반 시험 목록
@router.get("/class/{class_id}")
def get_tests_by_class(class_id: int, db: Session = Depends(get_db)):
    tests = db.query(TestModel).filter(TestModel.class_id == class_id).all()
    if not tests:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 반의 시험이 없습니다"}
        }
    return {
        "success": True,
        "data": [
            {
                "id": t.id,
                "subject_id": t.subject_id,
                "test_name": t.test_name,
                "test_date": str(t.test_date),
                "class_id": t.class_id,
                "subject_name": t.subject_name
            }
            for t in tests
        ],
        "message": "특정 반 시험 목록 조회 성공"
    }


# ✅ [READ] 특정 과목 시험 목록
@router.get("/subject/{subject_id}")
def get_tests_by_subject(subject_id: int, db: Session = Depends(get_db)):
    tests = db.query(TestModel).filter(TestModel.subject_id == subject_id).all()
    if not tests:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 과목 시험이 없습니다"}
        }
    return {
        "success": True,
        "data": [
            {
                "id": t.id,
                "subject_id": t.subject_id,
                "test_name": t.test_name,
                "test_date": str(t.test_date),
                "class_id": t.class_id,
                "subject_name": t.subject_name
            }
            for t in tests
        ],
        "message": "특정 과목 시험 목록 조회 성공"
    }


# ✅ [READ] 다가오는 시험 일정 조회
@router.get("/upcoming")
def get_upcoming_tests(db: Session = Depends(get_db)):
    from datetime import date
    today = date.today()
    tests = db.query(TestModel).filter(TestModel.test_date >= today).order_by(TestModel.test_date).all()
    return {
        "success": True,
        "data": [
            {
                "id": t.id,
                "subject_id": t.subject_id,
                "test_name": t.test_name,
                "test_date": str(t.test_date),
                "class_id": t.class_id,
                "subject_name": t.subject_name
            }
            for t in tests
        ],
        "message": "다가오는 시험 일정 조회 완료"
    }


# ==========================================================
# [3단계] 혼합 라우터
# ==========================================================

# ✅ [SUMMARY] 특정 시험 요약 (응시자 수, 평균 점수)
@router.get("/{test_id}/summary")
def get_test_summary(test_id: int, db: Session = Depends(get_db)):
    avg_score, count = db.query(
        func.avg(TestScoreModel.score), func.count(TestScoreModel.id)
    ).filter(TestScoreModel.test_id == test_id).first()
    if count == 0:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 시험의 점수가 없습니다"}
        }
    return {
        "success": True,
        "data": {
            "test_id": test_id,
            "average_score": float(avg_score) if avg_score else 0,
            "student_count": count
        },
        "message": "시험 요약 조회 성공"
    }


# ✅ [READ] 특정 시험 응시 학생 목록
@router.get("/{test_id}/students")
def get_test_students(test_id: int, db: Session = Depends(get_db)):
    results = db.query(StudentModel.student_name, TestScoreModel.score).join(
        TestScoreModel, TestScoreModel.student_id == StudentModel.id
    ).filter(TestScoreModel.test_id == test_id).all()
    if not results:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 시험 응시 기록이 없습니다"}
        }
    return {
        "success": True,
        "data": [{"name": name, "score": score} for name, score in results],
        "message": "시험 응시 학생 목록 조회 성공"
    }


# ==========================================================
# [4단계] 완전 동적 라우터
# ==========================================================

# ✅ [READ] 특정 시험 조회
@router.get("/{test_id}")
def read_test(test_id: int, db: Session = Depends(get_db)):
    test = db.query(TestModel).filter(TestModel.id == test_id).first()
    if not test:
        return {
            "success": False,
            "error": {"code": 404, "message": "시험 정보를 찾을 수 없습니다"}
        }
    return {
        "success": True,
        "data": {
            "id": test.id,
            "subject_id": test.subject_id,
            "test_name": test.test_name,
            "test_date": str(test.test_date),
            "class_id": test.class_id,
            "subject_name": test.subject_name
        },
        "message": "시험 상세 조회 성공"
    }


# ✅ [UPDATE] 시험 정보 수정
@router.put("/{test_id}")
def update_test(test_id: int, updated: TestCreate, db: Session = Depends(get_db)):
    test = db.query(TestModel).filter(TestModel.id == test_id).first()
    if not test:
        return {
            "success": False,
            "error": {"code": 404, "message": "시험 정보를 찾을 수 없습니다"}
        }

    for key, value in updated.model_dump().items():
        setattr(test, key, value)

    db.commit()
    db.refresh(test)
    return {
        "success": True,
        "data": {
            "id": test.id,
            "subject_id": test.subject_id,
            "test_name": test.test_name,
            "test_date": str(test.test_date),
            "class_id": test.class_id,
            "subject_name": test.subject_name
        },
        "message": "시험 정보가 성공적으로 수정되었습니다"
    }


# ✅ [DELETE] 시험 삭제
@router.delete("/{test_id}")
def delete_test(test_id: int, db: Session = Depends(get_db)):
    test = db.query(TestModel).filter(TestModel.id == test_id).first()
    if not test:
        return {
            "success": False,
            "error": {"code": 404, "message": "시험 정보를 찾을 수 없습니다"}
        }

    db.delete(test)
    db.commit()
    return {
        "success": True,
        "data": {"test_id": test_id},
        "message": "시험이 성공적으로 삭제되었습니다"
    }
