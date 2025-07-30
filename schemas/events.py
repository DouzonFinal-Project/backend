from pydantic import BaseModel
from datetime import date

# ✅ 학사일정 등록용 (POST 요청 시 사용)
class EventCreate(BaseModel):
    title: str                # 일정 제목
    date: date               # 일정 날짜
    location: str            # 장소
    target: str              # 대상 (예: 전교생, 3학년 등)

# ✅ 학사일정 조회용 (GET 응답 시 사용)
class Event(BaseModel):
    event_id: int            # 일정 고유 ID (자동 생성)
    title: str
    date: date
    location: str
    target: str

    class Config:
        orm_mode = True      # SQLAlchemy 모델과 호환
