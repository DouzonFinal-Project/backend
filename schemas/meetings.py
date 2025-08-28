from pydantic import BaseModel
from typing import Optional
from datetime import date, time

from schemas.students import Student
from schemas.teachers import Teacher


# ==========================================================
# [입력용 스키마]
# ==========================================================
class MeetingCreate(BaseModel):
    title: str                               # 상담 제목
    meeting_type: Optional[str] = None       # 상담 유형 (상담, 회의 등)
    student_id: Optional[int] = None         # 학생 ID (없을 수도 있음)
    teacher_id: Optional[int] = None         # 교사 ID (회의는 담임교사와 무관할 수도 있음)
    date: date                               # 상담 날짜
    time: time                               # 상담 시간
    location: Optional[str] = None           # 상담 장소


# ==========================================================
# [출력용 스키마]
# ==========================================================
class Meeting(MeetingCreate):
    id: int                                  # PK
    student: Optional[Student] = None        # 학생 객체 (없을 수도 있음)
    teacher: Optional[Teacher] = None        # 교사 객체 (없을 수도 있음)

    class Config:
        from_attributes = True
