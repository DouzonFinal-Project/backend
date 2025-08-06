from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    subject = Column(String(100))
    role = Column(String(50))
    is_homeroom = Column(Boolean, default=False)
    homeroom_class = Column(String(50))
    class_id = Column(Integer, ForeignKey("classes.id"))

    # ✅ 이 교사가 담임을 맡은 학급들 (ONE-TO-MANY 방향)
    classes = relationship(
        "Class",
        back_populates="teacher",
        foreign_keys="Class.teacher_id"
    )

    # ✅ 이 교사가 담임으로 설정된 학급 객체 (자신이 속한 학급 1개)
    class_ = relationship(
        "Class",
        foreign_keys=[class_id]
    )
