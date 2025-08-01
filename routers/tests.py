from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.tests import Test as TestModel
from schemas.tests import Test as TestSchema

router = APIRouter(prefix="/tests", tags=["시험정보"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 시험 추가
@router.post("/", response_model=TestSchema)
def create_test(test: TestSchema, db: Session = Depends(get_db)):
    db_test = TestModel(**test.model_dump())
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test

# ✅ [READ] 전체 시험 조회
@router.get("/", response_model=list[TestSchema])
def read_tests(db: Session = Depends(get_db)):
    return db.query(TestModel).all()

# ✅ [READ] 시험 상세 조회
@router.get("/{test_id}", response_model=TestSchema)
def read_test(test_id: int, db: Session = Depends(get_db)):
    test = db.query(TestModel).filter(TestModel.id == test_id).first()
    if test is None:
        raise HTTPException(status_code=404, detail="시험 정보를 찾을 수 없습니다")
    return test

# ✅ [UPDATE] 시험 수정
@router.put("/{test_id}", response_model=TestSchema)
def update_test(test_id: int, updated: TestSchema, db: Session = Depends(get_db)):
    test = db.query(TestModel).filter(TestModel.id == test_id).first()
    if test is None:
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
    if test is None:
        raise HTTPException(status_code=404, detail="시험 정보를 찾을 수 없습니다")
    db.delete(test)
    db.commit()
    return {"message": "시험 정보가 성공적으로 삭제되었습니다"}
