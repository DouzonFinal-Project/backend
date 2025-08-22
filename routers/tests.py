from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.db import SessionLocal
from models.tests import Test as TestModel
from models.test_scores import TestScore as TestScoreModel
from models.students import Student as StudentModel
from schemas.tests import Test, TestCreate

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
@router.post("/", response_model=Test)
def create_test(new_test: TestCreate, db: Session = Depends(get_db)):
    db_test = TestModel(**new_test.model_dump())
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test

# ✅ [READ] 전체 시험 목록
@router.get("/", response_model=list[Test])
def read_tests(db: Session = Depends(get_db)):
    return db.query(TestModel).all()

# ==========================================================
# [2단계] 정적 라우터
# ==========================================================

# ✅ [READ] 특정 반 시험 목록
@router.get("/class/{class_id}", response_model=list[Test])
def get_tests_by_class(class_id: int, db: Session = Depends(get_db)):
    tests = db.query(TestModel).filter(TestModel.class_id == class_id).all()
    if not tests:
        raise HTTPException(status_code=404, detail="해당 반의 시험이 없습니다")
    return tests

# ✅ [READ] 특정 과목 시험 목록
@router.get("/subject/{subject_id}", response_model=list[Test])
def get_tests_by_subject(subject_id: int, db: Session = Depends(get_db)):
    tests = db.query(TestModel).filter(TestModel.subject_id == subject_id).all()
    if not tests:
        raise HTTPException(status_code=404, detail="해당 과목 시험이 없습니다")
    return tests

# ✅ [READ] 다가오는 시험 일정 조회
@router.get("/upcoming", response_model=list[Test])
def get_upcoming_tests(db: Session = Depends(get_db)):
    from datetime import date
    today = date.today()
    tests = db.query(TestModel).filter(TestModel.date >= today).order_by(TestModel.date).all()
    return tests

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
        raise HTTPException(status_code=404, detail="해당 시험의 점수가 없습니다")
    return {"test_id": test_id, "average_score": avg_score, "student_count": count}

# ✅ [READ] 특정 시험 응시 학생 목록
@router.get("/{test_id}/students")
def get_test_students(test_id: int, db: Session = Depends(get_db)):
    results = db.query(StudentModel.student_name, TestScoreModel.score).join(
        TestScoreModel, TestScoreModel.student_id == StudentModel.id
    ).filter(TestScoreModel.test_id == test_id).all()
    if not results:
        raise HTTPException(status_code=404, detail="해당 시험 응시 기록이 없습니다")
    return [{"name": name, "score": score} for name, score in results]

# ==========================================================
# [4단계] 완전 동적 라우터
# ==========================================================

# ✅ [READ] 특정 시험 조회
@router.get("/{test_id}", response_model=Test)
def read_test(test_id: int, db: Session = Depends(get_db)):
    test = db.query(TestModel).filter(TestModel.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="시험 정보를 찾을 수 없습니다")
    return test

# ✅ [UPDATE] 시험 정보 수정
@router.put("/{test_id}", response_model=Test)
def update_test(test_id: int, updated: TestCreate, db: Session = Depends(get_db)):
    test = db.query(TestModel).filter(TestModel.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="시험 정보를 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(test, key, value)
    db.commit()
    db.refresh(test)
    return test

# ✅ [DELETE] 시험 삭제
@router.delete("/{test_id}")
def delete_test(test_id: int, db: Session = Depends(get_db)):
    test = db.query(TestModel).filter(TestModel.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="시험 정보를 찾을 수 없습니다")
    db.delete(test)
    db.commit()
    return {"message": "✅ 시험이 성공적으로 삭제되었습니다"}
