from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from database.db import Base

# ✅ 외래키 관계 대상 모델 import
from models.students import Student as StudentModel
from models.teachers import Teacher as TeacherModel

# ✅ 상담 및 면담 기록 테이블 정의
class Meeting(Base):
    __tablename__ = "meetings"  # 테이블명: meetings

    id = Column(Integer, primary_key=True, index=True)         # 상담 고유 ID (PK)
    title = Column(String(100), nullable=False)                # 상담 제목
    meeting_type = Column(String(50), nullable=False)          # 상담 유형 (예: 생활, 학업, 진로 등)
    date = Column(Date, nullable=False)                        # 상담 일자 (YYYY-MM-DD)
    time = Column(Time, nullable=False)                        # 상담 시간 (HH:MM)
    location = Column(String(100), nullable=True)              # 상담 장소

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)  # 상담 대상 학생 ID (FK)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)  # 상담 진행 교사 ID (FK)

    # ✅ 관계 설정: 학생 객체와의 ORM 관계
    student = relationship(StudentModel, backref="meetings", lazy="joined")

    # ✅ 관계 설정: 교사 객체와의 ORM 관계
    teacher = relationship(TeacherModel, backref="meetings", lazy="joined")
