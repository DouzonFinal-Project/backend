from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.db import SessionLocal
from models.events import Event as EventModel
from schemas.events import Event as EventSchema

router = APIRouter(prefix="/events", tags=["학사일정"])

# ==========================================================
# [공통] DB 세션 관리
# ==========================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================================
# [1단계] CRUD 기본 라우터
# ==========================================================

# ✅ [CREATE] 학사일정 추가
@router.post("/")
def create_event(event: EventSchema, db: Session = Depends(get_db)):
    db_event = EventModel(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return {
        "success": True,
        "data": {
            "id": db_event.id,
            "event_name": db_event.event_name,       # ✅ 수정
            "event_type": db_event.event_type,       # ✅ 추가
            "date": str(db_event.date),
            "description": db_event.description,
        },
        "message": "학사일정이 성공적으로 등록되었습니다"
    }

# ✅ [READ] 전체 학사일정 조회
@router.get("/")
def read_events(db: Session = Depends(get_db)):
    records = db.query(EventModel).all()
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "event_name": r.event_name,       # ✅ 수정
                "event_type": r.event_type,       # ✅ 추가
                "date": str(r.date),
                "description": r.description
            }
            for r in records
        ]
    }

# ==========================================================
# [2단계] 정적 라우터
# ==========================================================

# ✅ [MONTHLY] 특정 월 일정 조회
@router.get("/monthly")
def get_monthly_events(year: int, month: int, db: Session = Depends(get_db)):
    events = (
        db.query(EventModel)
        .filter(func.year(EventModel.date) == year)
        .filter(func.month(EventModel.date) == month)
        .all()
    )
    return {
        "success": True,
        "data": [
            {
                "id": e.id,
                "event_name": e.event_name,
                "event_type": e.event_type,
                "date": str(e.date),
                "description": e.description
            }
            for e in events
        ]
    }

# ✅ [WEEKLY] 특정 기간(주간) 일정 조회
@router.get("/weekly")
def get_weekly_events(start_date: str, end_date: str, db: Session = Depends(get_db)):
    events = (
        db.query(EventModel)
        .filter(EventModel.date.between(start_date, end_date))
        .all()
    )
    return {
        "success": True,
        "data": [
            {
                "id": e.id,
                "event_name": e.event_name,
                "event_type": e.event_type,
                "date": str(e.date),
                "description": e.description
            }
            for e in events
        ]
    }

# ==========================================================
# [3단계] 동적 라우터
# ==========================================================

# ✅ [READ] 단일 학사일정 조회
@router.get("/{event_id}")
def read_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if event is None:
        return {"success": False, "error": {"code": 404, "message": "학사일정을 찾을 수 없습니다"}}
    return {
        "success": True,
        "data": {
            "id": event.id,
            "event_name": event.event_name,
            "event_type": event.event_type,
            "date": str(event.date),
            "description": event.description
        }
    }

# ✅ [UPDATE] 학사일정 수정
@router.put("/{event_id}")
def update_event(event_id: int, updated: EventSchema, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if event is None:
        return {"success": False, "error": {"code": 404, "message": "학사일정을 찾을 수 없습니다"}}

    # 부분 업데이트 허용 + ID 변경 방지
    update_data = updated.model_dump(exclude_unset=True)
    if "id" in update_data:
        del update_data["id"]
        
    for key, value in updated.model_dump().items():
        setattr(event, key, value)

    db.commit()
    db.refresh(event)
    return {
        "success": True,
        "data": {
            "id": event.id,
            "event_name": event.event_name,
            "event_type": event.event_type,
            "date": str(event.date),
            "description": event.description
        },
        "message": "학사일정이 성공적으로 수정되었습니다"
    }

# ✅ [DELETE] 학사일정 삭제
@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if event is None:
        return {"success": False, "error": {"code": 404, "message": "학사일정을 찾을 수 없습니다"}}

    db.delete(event)
    db.commit()
    return {
        "success": True,
        "data": {"event_id": event_id},
        "message": "학사일정이 성공적으로 삭제되었습니다"
    }
