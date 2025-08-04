from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

# ✅ 외래키 관계 대상이 되는 Student, Teacher 모델을 직접 import
from models.students import Student as StudentModel
from models.teachers import Teacher as TeacherModel

# ✅ 상담 및 면담 기록 테이블 정의
class Meeting(Base):
    __tablename__ = "meetings"  # 테이블명: meetings

    id = Column(Integer, primary_key=True, index=True)        # 상담 고유 ID (PK)
    title = Column(String(100), nullable=False)               # 상담 제목
    meeting_type = Column(String(50))                         # 상담 유형 (예: 생활, 학업, 진로 등)

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)  # 상담 대상 학생 ID (FK)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)  # 상담 진행 교사 ID (FK)

    # ✅ 관계 설정: 학생 객체와의 ORM 관계
    # lazy="joined"를 통해 조회 시 즉시 student 테이블 join → 직렬화 오류 방지
    student = relationship(StudentModel, backref="meetings", lazy="joined")  

    # ✅ 관계 설정: 교사 객체와의 ORM 관계
    teacher = relationship(TeacherModel, backref="meetings", lazy="joined")
