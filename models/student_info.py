from sqlalchemy import Column, Integer, String
from database.db import Base

class StudentInfo(Base):
    __tablename__ = "student_info"

    student_id = Column(Integer, primary_key=True, index=True)         # 학생 고유 ID (Primary Key)
    student_name = Column(String(100), nullable=False)                 # 학생 이름
    gender = Column(String(10))                                        # 성별 (예: 남, 여)
    phone = Column(String(20))                                         # 연락처
    address = Column(String(200))                                      # 주소
