from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    grade = Column(Integer, nullable=False)
    class_num = Column(Integer, nullable=False)

    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    teacher = relationship(
        "Teacher",
        back_populates="classes",  # ✅ 교사 쪽에서 여러 학급을 가짐
        foreign_keys=[teacher_id]
    )
