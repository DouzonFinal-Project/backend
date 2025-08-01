from sqlalchemy import Column, Integer, Float, String
from database.db import Base

class Grade(Base):
    __tablename__ = "grades"  # 성적 요약 테이블

    id = Column(Integer, primary_key=True, index=True)     # 성적 고유 ID (Primary Key)
    student_id = Column(Integer, nullable=False)           # 학생 ID
    subject_id = Column(Integer, nullable=False)           # 과목 ID
    term = Column(Integer, nullable=False)                 # 학기
    average_score = Column(Float)                          # 평균 점수
    grade_letter = Column(String(10))                      # 성적 등급 (예: A, B, C)
