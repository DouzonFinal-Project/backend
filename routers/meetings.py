from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.meetings import Meeting as MeetingModel
from schemas.meetings import Meeting, MeetingCreate

router = APIRouter(prefix="/meetings", tags=["상담기록"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 상담기록 추가
@router.post("/", response_model=Meeting)
def create_meeting(meeting: MeetingCreate, db: Session = Depends(get_db)):
    db_meeting = MeetingModel(**meeting.model_dump())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

# ✅ [READ] 전체 상담기록 조회
@router.get("/", response_model=list[Meeting])
def read_meetings(db: Session = Depends(get_db)):
    return db.query(MeetingModel).all()

# ✅ [READ] 상담기록 상세 조회
@router.get("/{meeting_id}", response_model=Meeting)
def read_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    if meeting is None:
        raise HTTPException(status_code=404, detail="상담기록을 찾을 수 없습니다")
    return meeting

# ✅ [UPDATE] 상담기록 수정
@router.put("/{meeting_id}", response_model=Meeting)
def update_meeting(meeting_id: int, updated: MeetingCreate, db: Session = Depends(get_db)):
    meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    if meeting is None:
        raise HTTPException(status_code=404, detail="상담기록을 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(meeting, key, value)
    db.commit()
    db.refresh(meeting)
    return meeting

# ✅ [DELETE] 상담기록 삭제
@router.delete("/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    if meeting is None:
        raise HTTPException(status_code=404, detail="상담기록을 찾을 수 없습니다")
    db.delete(meeting)
    db.commit()
    return {"message": "상담기록이 성공적으로 삭제되었습니다"}
