from pydantic import BaseModel
from typing import Optional
from datetime import date, time

class Event(BaseModel):
    id: Optional[int] = None                 # 일정 고유 ID (생성 시 None 허용)
    event_name: str                          # 일정 이름
    event_type: Optional[str] = None         # 일정 유형
    start_date: date                         # 시작 날짜
    end_date: Optional[date] = None          # 종료 날짜 (NULL 가능)
    start_time: Optional[time] = None        # 시작 시간 (NULL 가능)
    end_time: Optional[time] = None          # 종료 시간 (NULL 가능)
    description: Optional[str] = None        # 상세 설명

    class Config:
        from_attributes = True
