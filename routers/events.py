from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.db import SessionLocal
from models.events import Event as EventModel
from schemas.events import Event as EventSchema

router = APIRouter(prefix="/events", tags=["events"])

# ==========================================================
# [공통] DB 세션 관리
# - 모든 요청에서 DB 연결을 열고 닫는 역할
# - connection leak 방지를 위해 try/finally 사용
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
# - 새로운 학사일정을 생성할 때 사용
# - 예: 개학일, 시험일, 행사일 등록
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
            "title": db_event.title,
            "date": str(db_event.date),
            "description": db_event.description,
            "message": "Event created successfully"
        }
    }

# ✅ [READ] 전체 학사일정 조회
# - 등록된 모든 학사일정 데이터를 조회
# - 예: 연간 학사 일정표 출력
@router.get("/")
def read_events(db: Session = Depends(get_db)):
    records = db.query(EventModel).all()
    return {
        "success": True,
        "data": [
            {"id": r.id, "title": r.title, "date": str(r.date), "description": r.description}
            for r in records
        ]
    }

# ==========================================================
# [2단계] 정적 라우터
# ==========================================================

# ✅ [MONTHLY] 특정 월 일정 조회
# - 지정된 연도와 월의 학사일정을 반환
# - 학급별/학교별 월간 캘린더 조회에 활용
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
            {"id": e.id, "title": e.title, "date": str(e.date), "description": e.description}
            for e in events
        ]
    }

# ✅ [WEEKLY] 특정 기간(주간) 일정 조회
# - 시작일~종료일 범위 내의 학사일정 반환
# - 주간 계획표, 주간 회의 자료 등에 활용
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
            {"id": e.id, "title": e.title, "date": str(e.date), "description": e.description}
            for e in events
        ]
    }

# ==========================================================
# [3단계] 동적 라우터 (맨 마지막 배치)
# ==========================================================

# ✅ [READ] 학사일정 상세 조회
# - 단일 학사일정 정보를 ID 기준으로 반환
@router.get("/{event_id}")
def read_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if event is None:
        return {"success": False, "error": {"code": 404, "message": "Event not found"}}
    return {
        "success": True,
        "data": {
            "id": event.id,
            "title": event.title,
            "date": str(event.date),
            "description": event.description
        }
    }

# ✅ [UPDATE] 학사일정 수정
# - 기존 학사일정의 제목, 날짜, 설명을 변경
@router.put("/{event_id}")
def update_event(event_id: int, updated: EventSchema, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if event is None:
        return {"success": False, "error": {"code": 404, "message": "Event not found"}}

    for key, value in updated.model_dump().items():
        setattr(event, key, value)

    db.commit()
    db.refresh(event)
    return {
        "success": True,
        "data": {
            "id": event.id,
            "title": event.title,
            "date": str(event.date),
            "description": event.description,
            "message": "Event updated successfully"
        }
    }

# ✅ [DELETE] 학사일정 삭제
# - 불필요하거나 잘못 등록된 학사일정을 삭제
@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if event is None:
        return {"success": False, "error": {"code": 404, "message": "Event not found"}}

    db.delete(event)
    db.commit()
    return {
        "success": True,
        "data": {
            "event_id": event_id,
            "message": "Event deleted successfully"
        }
    }
