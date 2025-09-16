# schemas/school_report.py
from pydantic import BaseModel
from typing import Optional

class SchoolReport(BaseModel):
    id: int                                       # 생활기록부 고유 ID
    year: int                                     # 연도
    semester: int                                 # 학기
    student_id: int                               # 학생 ID
    behavior_summary: Optional[str] = None        # 행동 특성 요약
    peer_relation: Optional[str] = None           # 또래 관계
    career_aspiration: Optional[str] = None       # 진로 희망
    teacher_feedback: Optional[str] = None        # 종합 의견

    class Config:
        from_attributes = True
