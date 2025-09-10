from pydantic import BaseModel
from datetime import date, time
from typing import Optional

# ==========================================================
# [입력용 스키마]
# ==========================================================
class MeetingCreate(BaseModel):
    title: str                     # 상담 제목
    meeting_type: str              # 상담 유형
    date: date                     # 상담 일자
    time: time                     # 상담 시간
    location: Optional[str] = None # 상담 장소
    student_id: int                # 학생 ID
    teacher_id: int                # 교사 ID

# ==========================================================
# [출력용 스키마]
# ==========================================================
class Meeting(MeetingCreate):
    id: int                        # 상담 고유 ID

    class Config:
        from_attributes = True
