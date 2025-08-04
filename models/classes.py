from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class Class(Base):
    __tablename__ = "classes"  # 학급 정보 테이블

    id = Column(Integer, primary_key=True, index=True)   # 학급 고유 ID (Primary Key)
    grade = Column(Integer, nullable=False)              # 학년
    class_num = Column(Integer, nullable=False)          # 반 번호
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)  # 담임 교사 ID (teachers 테이블의 id와 연동하는 외래 키)
    teacher = relationship("Teacher", backref="classes")  # 교사 객체와의 ORM 관계 설정
