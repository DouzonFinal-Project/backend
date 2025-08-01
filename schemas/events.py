from pydantic import BaseModel
from typing import Optional
from datetime import date

class Event(BaseModel):
    id: int                                  # 일정 고유 ID
    event_name: str                          # 일정 이름
    event_type: Optional[str] = None         # 일정 유형
    date: date                               # 날짜
    description: Optional[str] = None        # 상세 설명

    class Config:
        orm_mode = True
