from pydantic import BaseModel
from typing import Optional

class TestScore(BaseModel):
    id: int                                  # 시험 성적 고유 ID
    test_id: int                             # 시험 ID
    student_id: int                          # 학생 ID
    score: float                             # 점수
    subject_name: Optional[str] = None       # 과목 이름 (중복 저장용)

    class Config:
        from_attributes = True
