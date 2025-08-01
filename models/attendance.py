from sqlalchemy import Column, Integer, String, Date
from database.db import Base

class Attendance(Base):
    __tablename__ = "attendance"  # 출결 기록 테이블

    id = Column(Integer, primary_key=True, index=True)         # 출결 고유 ID (Primary Key)
    student_id = Column(Integer, nullable=False)               # 학생 ID (students 테이블과 연동)
    date = Column(Date, nullable=False)                        # 날짜
    status = Column(String(20), nullable=False)                # 출결 상태 (예: 출석, 결석, 지각)
    reason = Column(String(200))                               # 사유 (결석/조퇴 등 상세 이유)
