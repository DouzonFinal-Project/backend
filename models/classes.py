from sqlalchemy import Column, Integer
from database.db import Base

class Class(Base):
    __tablename__ = "classes"  # 학급 정보 테이블

    id = Column(Integer, primary_key=True, index=True)   # 학급 고유 ID (Primary Key)
    grade = Column(Integer, nullable=False)              # 학년
    class_num = Column(Integer, nullable=False)          # 반 번호
    teacher_id = Column(Integer, nullable=False)         # 담임 교사 ID (teachers 테이블과 연동)
