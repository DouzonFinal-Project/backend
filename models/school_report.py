from sqlalchemy import Column, Integer, String, Text, ForeignKey
from database.db import Base

class SchoolReport(Base):
    __tablename__ = "school_report"

    report_id = Column(Integer, primary_key=True, index=True)         # 고유 보고서 ID (자동 생성)
    student_id = Column(Integer, ForeignKey("student_info.student_id"))  # 학생 ID (외래키)
    student_name = Column(String(100), nullable=False)                # 학생 이름
    behavior_summary = Column(Text)                                   # 생활 태도 요약
    career_aspiration = Column(Text)                                  # 진로 희망
    teacher_feedback = Column(Text)                                   # 교사 종합 의견
