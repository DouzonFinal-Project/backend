from sqlalchemy import Column, Integer, String
from database.db import Base

class Student(Base):
    __tablename__ = "students"  # 학생 기본 정보 테이블

    id = Column(Integer, primary_key=True, index=True)               # 고유 학생 ID (Primary Key)
    student_name = Column(String(100), nullable=False)              # 학생 이름
    class_id = Column(Integer, nullable=False)                      # 소속 반 ID (classes 테이블과 연동)
    gender = Column(String(10))                                     # 성별 (예: 남, 여)
    phone = Column(String(20))                                      # 학생 연락처
    address = Column(String(200))                                   # 주소
