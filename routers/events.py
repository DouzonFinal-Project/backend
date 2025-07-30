from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.events import Event as EventModel
from schemas.events import Event, EventCreate
from database.db import SessionLocal

router = APIRouter(prefix="/events", tags=["학사 일정"])

# ✅ DB 세션 주입 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 학사 일정 등록
@router.post("/", response_model=Event)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    db_event = EventModel(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

# ✅ [READ] 전체 일정 조회
@router.get("/", response_model=list[Event])
def read_events(db: Session = Depends(get_db)):
    return db.query(EventModel).all()

# ✅ [READ] 특정 일정 조회
@router.get("/{event_id}", response_model=Event)
def read_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
    return event

# ✅ [UPDATE] 학사 일정 수정
@router.put("/{event_id}", response_model=Event)
def update_event(event_id: int, updated: EventCreate, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
    for key, value in updated.dict().items():
        setattr(event, key, value)
    db.commit()
    db.refresh(event)
    return event

# ✅ [DELETE] 일정 삭제
@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
    db.delete(event)
    db.commit()
    return {"message": "학사 일정이 삭제되었습니다."}
