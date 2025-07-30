from sqlalchemy import Column, Integer, String, Float
from database.db import Base

class Grade(Base):
    __tablename__ = "grades"

    grade_id = Column(Integer, primary_key=True, index=True)          # 성적 고유 ID (Auto Increment, PK)
    student_id = Column(Integer, index=True)                          # 학생 고유 ID
    student_name = Column(String(100))                                # 학생 이름
    subject = Column(String(50))                                      # 과목명 (예: 수학, 과학)
    test_score = Column(Float)                                        # 시험 점수
    assignment_score = Column(Float)                                  # 과제 점수
    total_score = Column(Float)                                       # 총점 (합산 or 평균)
