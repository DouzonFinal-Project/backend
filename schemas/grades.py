from pydantic import BaseModel
from typing import Optional

# ✅ 성적 등록용 (POST 요청)
class GradeCreate(BaseModel):
    student_id: int                    # 학생 고유 ID
    student_name: str                 # 학생 이름
    subject: str                      # 과목명
    test_score: float                 # 시험 점수
    assignment_score: float          # 과제 점수
    total_score: float                # 총점

# ✅ 성적 조회/응답용 (GET 응답)
class Grade(BaseModel):
    grade_id: int                     # 성적 고유 ID (DB 자동 생성)
    student_id: int
    student_name: str
    subject: str
    test_score: float
    assignment_score: float
    total_score: float

    class Config:
        orm_mode = True               # SQLAlchemy 모델과 호환
