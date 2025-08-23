from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)      # 학급 고유 ID (PK)
    grade = Column(Integer, nullable=False)                 # 학년 (예: 1학년, 2학년 등)
    class_num = Column(Integer, nullable=False)             # 반 번호 (예: 1반, 2반 등)

    # ==========================================================
    # [관계 설정]
    # ==========================================================

    # ✅ 담임 교사 ID (FK)
    #    - teachers.id를 참조
    teacher_id = Column(Integer, ForeignKey("teachers.id"))

    # ✅ 담임 교사와의 관계 (N:1)
    #    - Teacher 모델의 classes 필드와 연결 (back_populates)
    #    - 한 교사는 여러 학급을 가질 수 있음 (1:N)
    teacher = relationship(
        "Teacher",
        back_populates="classes",
        foreign_keys=[teacher_id]
    )
