from sqlalchemy import Column, Integer, String, Date
from database.db import Base

class Test(Base):
    __tablename__ = "tests"  # 시험 정보 테이블

    id = Column(Integer, primary_key=True, index=True)        # 시험 고유 ID
    subject_id = Column(Integer, nullable=False)             # 과목 ID
    test_name = Column(String(100), nullable=False)          # 시험명
    test_date = Column(Date, nullable=False)                 # 시험 날짜
    class_id = Column(Integer, nullable=False)               # 시험 대상 학급 ID
    subject_name = Column(String(100))                       # 과목 이름 (중복 저장)
