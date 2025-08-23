from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base
from models.classes import Class   # ✅ Class 직접 import (중요!)

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)      # 교사 고유 ID (PK)
    name = Column(String(100), nullable=False)              # 교사 이름
    email = Column(String(100), unique=True)                # 이메일
    phone = Column(String(20))                              # 전화번호
    subject = Column(String(100))                           # 담당 과목
    role = Column(String(50))                               # 역할
    is_homeroom = Column(Boolean, default=False)            # 담임 여부
    homeroom_class = Column(String(50))                     # 담임 학급명
    class_id = Column(Integer, ForeignKey("classes.id"))    # 소속 학급 ID (FK)

    # ✅ 이 교사가 맡은 학급들 (1:N 관계)
    classes = relationship(
        "Class",
        back_populates="teacher",
        foreign_keys=[Class.teacher_id]   # ✅ 컬럼 직접 참조
    )

    # ✅ 이 교사가 소속된 학급 (1:1 관계)
    class_ = relationship(
        "Class",
        foreign_keys=[class_id]
    )
