from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)              # 학급 고유 ID (Primary Key)
    grade = Column(Integer, nullable=False)                         # 학년 (예: 1학년, 2학년 등)
    class_num = Column(Integer, nullable=False)                     # 반 번호 (예: 1반, 2반 등)

    teacher_id = Column(Integer, ForeignKey("teachers.id"))         # 담임 교사 ID (teachers 테이블과 연결됨)
    teacher = relationship(
        "Teacher",
        back_populates="classes",                                   # 교사 모델에서 연결된 classes 필드와 매핑됨 (1:N 관계)
        foreign_keys=[teacher_id]                                   # 이 필드가 외래 키임을 명시
    )
