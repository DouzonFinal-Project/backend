from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.events import Event as EventModel
from schemas.events import Event as EventSchema

router = APIRouter(prefix="/events", tags=["학사일정"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 학사일정 추가
@router.post("/", response_model=EventSchema)
def create_event(event: EventSchema, db: Session = Depends(get_db)):
    db_event = EventModel(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

# ✅ [READ] 전체 학사일정 조회
@router.get("/", response_model=list[EventSchema])
def read_events(db: Session = Depends(get_db)):
    return db.query(EventModel).all()

# ✅ [READ] 학사일정 상세 조회
@router.get("/{event_id}", response_model=EventSchema)
def read_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="학사일정을 찾을 수 없습니다")
    return event

# ✅ [UPDATE] 학사일정 수정
@router.put("/{event_id}", response_model=EventSchema)
def update_event(event_id: int, updated: EventSchema, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="학사일정을 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(event, key, value)
    db.commit()
    db.refresh(event)
    return event

# ✅ [DELETE] 학사일정 삭제
@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="학사일정을 찾을 수 없습니다")
    db.delete(event)
    db.commit()
    return {"message": "학사일정이 성공적으로 삭제되었습니다"}
