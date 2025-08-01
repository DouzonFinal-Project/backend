from pydantic import BaseModel
from typing import Optional

class Grade(BaseModel):
    id: int                                  # 성적 고유 ID
    student_id: int                          # 학생 ID
    subject_id: int                          # 과목 ID
    term: int                                # 학기
    average_score: Optional[float] = None    # 평균 점수
    grade_letter: Optional[str] = None       # 성적 등급 (예: A, B, C)

    class Config:
        orm_mode = True
