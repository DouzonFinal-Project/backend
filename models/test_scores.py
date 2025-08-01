from sqlalchemy import Column, Integer, Float, String
from database.db import Base

class TestScore(Base):
    __tablename__ = "test_scores"  # 시험 성적 테이블

    id = Column(Integer, primary_key=True, index=True)     # 시험 성적 고유 ID (Primary Key)
    test_id = Column(Integer, nullable=False)              # 시험 ID (tests 테이블과 연동)
    student_id = Column(Integer, nullable=False)           # 학생 ID (students 테이블과 연동)
    score = Column(Float, nullable=False)                  # 시험 점수
    subject_name = Column(String(100))                     # 과목 이름 (참고용, 중복 저장 가능)
