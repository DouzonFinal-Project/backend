from pydantic import BaseModel
from typing import Optional

class Meeting(BaseModel):
    id: int                                  # 상담 고유 ID
    title: str                               # 상담 제목
    meeting_type: Optional[str] = None       # 상담 유형
    student_id: int                          # 학생 ID
    teacher_id: int                          # 교사 ID

    class Config:
        orm_mode = True
