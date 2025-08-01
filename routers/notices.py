from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.notices import Notice as NoticeModel
from schemas.notices import Notice as NoticeSchema

router = APIRouter(prefix="/notices", tags=["공지사항"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 공지사항 추가
@router.post("/", response_model=NoticeSchema)
def create_notice(notice: NoticeSchema, db: Session = Depends(get_db)):
    db_notice = NoticeModel(**notice.model_dump())
    db.add(db_notice)
    db.commit()
    db.refresh(db_notice)
    return db_notice

# ✅ [READ] 전체 공지사항 조회
@router.get("/", response_model=list[NoticeSchema])
def read_notices(db: Session = Depends(get_db)):
    return db.query(NoticeModel).all()

# ✅ [READ] 공지사항 상세 조회
@router.get("/{notice_id}", response_model=NoticeSchema)
def read_notice(notice_id: int, db: Session = Depends(get_db)):
    notice = db.query(NoticeModel).filter(NoticeModel.id == notice_id).first()
    if notice is None:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")
    return notice

# ✅ [UPDATE] 공지사항 수정
@router.put("/{notice_id}", response_model=NoticeSchema)
def update_notice(notice_id: int, updated: NoticeSchema, db: Session = Depends(get_db)):
    notice = db.query(NoticeModel).filter(NoticeModel.id == notice_id).first()
    if notice is None:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(notice, key, value)
    db.commit()
    db.refresh(notice)
    return notice

# ✅ [DELETE] 공지사항 삭제
@router.delete("/{notice_id}")
def delete_notice(notice_id: int, db: Session = Depends(get_db)):
    notice = db.query(NoticeModel).filter(NoticeModel.id == notice_id).first()
    if notice is None:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")
    db.delete(notice)
    db.commit()
    return {"message": "공지사항이 성공적으로 삭제되었습니다"}
