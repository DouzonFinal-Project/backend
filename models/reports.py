from sqlalchemy import Column, Integer, String, Date
from database.db import Base

class Report(Base):
    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # 고유 식별자
    student_id = Column(Integer, nullable=False)         # 학생 ID
    student_name = Column(String(100), nullable=False)   # 학생 이름
    date = Column(Date, nullable=False)                  # 상담 일자
    type = Column(String(50), nullable=False)            # 상담 유형 (예: 생활, 진로 등)
    teacher_note = Column(String(1000))                  # 교사 작성 노트
