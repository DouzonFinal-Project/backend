from pydantic import BaseModel
from typing import Optional
from datetime import date

class Attendance(BaseModel):
    id: int                                  # 출결 고유 ID
    student_id: int                          # 학생 ID
    date: date                               # 날짜
    status: str                              # 출결 상태 (예: 출석, 지각, 결석)
    reason: Optional[str] = None             # 결석/조퇴 사유

    class Config:
        orm_mode = True
