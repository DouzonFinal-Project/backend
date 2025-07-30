from sqlalchemy import Column, Integer, String, Date
from database.db import Base

class StudentAttendance(Base):
    __tablename__ = "student_attendance"

    id = Column(Integer, primary_key=True, index=True)          # 출결 고유 ID (Auto Increment, PK)
    student_id = Column(Integer, index=True)                    # 학생 고유 ID (FK로 연결 가능)
    student_name = Column(String(100))                          # 학생 이름
    date = Column(Date)                                         # 출결 일자
    status = Column(String(20))                                 # 출결 상태 (예: 출석, 결석, 지각, 조퇴 등)
    reason = Column(String(200))                                # 출결 사유 (예: 병원 방문, 가족 행사 등)
