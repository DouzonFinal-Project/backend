from sqlalchemy import Column, Integer, String
from database.db import Base

class Subject(Base):
    __tablename__ = "subjects"  # 과목 정보 테이블

    id = Column(Integer, primary_key=True, index=True)         # 과목 고유 ID (Primary Key)
    name = Column(String(100), nullable=False)                # 과목 이름 (예: 수학, 영어)
    category = Column(String(50))                             # 과목 분류 (예: 필수, 선택)
