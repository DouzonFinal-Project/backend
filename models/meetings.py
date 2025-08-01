from sqlalchemy import Column, Integer, String
from database.db import Base

class Meeting(Base):
    __tablename__ = "meetings"  # 상담 및 면담 기록 테이블

    id = Column(Integer, primary_key=True, index=True)        # 상담 고유 ID (Primary Key)
    title = Column(String(100), nullable=False)              # 상담 제목
    meeting_type = Column(String(50))                        # 상담 유형 (예: 생활, 학업, 진로)
    student_id = Column(Integer, nullable=False)             # 학생 ID (students 테이블과 연동)
    teacher_id = Column(Integer, nullable=False)             # 교사 ID (teachers 테이블과 연동)
