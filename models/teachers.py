from sqlalchemy import Column, Integer, String
from database.db import Base

class Teacher(Base):
    __tablename__ = "teachers"  # 교사 정보 테이블

    id = Column(Integer, primary_key=True, index=True)               # 고유 교사 ID (Primary Key)
    name = Column(String(100), nullable=False)                      # 교사 이름
    email = Column(String(100), unique=True)                        # 이메일 주소
    phone = Column(String(20))                                      # 연락처
    subject = Column(String(100))                                   # 담당 과목 이름
