from fastapi import APIRouter, Depends, HTTPException
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

# ✅ [CREATE] 시험 성적 추가
@router.post("/", response_model=TestScoreSchema)
def create_test_score(score: TestScoreSchema, db: Session = Depends(get_db)):
    db_score = TestScoreModel(**score.model_dump())
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    return db_score

# ✅ [READ] 전체 성적 조회
@router.get("/", response_model=list[TestScoreSchema])
def read_test_scores(db: Session = Depends(get_db)):
    return db.query(TestScoreModel).all()

# ✅ [READ] 성적 상세 조회
@router.get("/{score_id}", response_model=TestScoreSchema)
def read_test_score(score_id: int, db: Session = Depends(get_db)):
    score = db.query(TestScoreModel).filter(TestScoreModel.id == score_id).first()
    if score is None:
        raise HTTPException(status_code=404, detail="시험 성적을 찾을 수 없습니다")
    return score

# ✅ [UPDATE] 성적 수정
@router.put("/{score_id}", response_model=TestScoreSchema)
def update_test_score(score_id: int, updated: TestScoreSchema, db: Session = Depends(get_db)):
    score = db.query(TestScoreModel).filter(TestScoreModel.id == score_id).first()
    if score is None:
        raise HTTPException(status_code=404, detail="시험 성적을 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(score, key, value)
    db.commit()
    db.refresh(score)
    return score

# ✅ [DELETE] 성적 삭제
@router.delete("/{score_id}")
def delete_test_score(score_id: int, db: Session = Depends(get_db)):
    score = db.query(TestScoreModel).filter(TestScoreModel.id == score_id).first()
    if score is None:
        raise HTTPException(status_code=404, detail="시험 성적을 찾을 수 없습니다")
    db.delete(score)
    db.commit()
    return {"message": "시험 성적이 성공적으로 삭제되었습니다"}
