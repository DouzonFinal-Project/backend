# models/school_report.py
from sqlalchemy import Column, Integer, String
from database.db import Base

class SchoolReport(Base):
    __tablename__ = "school_report"  # 생활기록부 테이블

    id = Column(Integer, primary_key=True, index=True)         # 고유 ID
    year = Column(Integer, nullable=False)                    # 연도
    semester = Column(Integer, nullable=False)                # 학기
    student_id = Column(Integer, nullable=False)              # 학생 ID
    behavior_summary = Column(String(1000))                   # 행동 특성 요약
    peer_relation = Column(String(500))                       # 또래 관계
    career_aspiration = Column(String(500))                   # 진로 희망
    teacher_feedback = Column(String(1000))                   # 종합 의견 (담임)
