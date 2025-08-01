from sqlalchemy import Column, Integer, String, Date
from database.db import Base

class Event(Base):
    __tablename__ = "events"  # 학사 일정 테이블

    id = Column(Integer, primary_key=True, index=True)      # 일정 고유 ID (Primary Key)
    event_name = Column(String(100), nullable=False)        # 행사/일정 이름 (예: 체육대회)
    event_type = Column(String(50))                         # 일정 유형 (예: 공휴일, 수업, 행사)
    date = Column(Date, nullable=False)                     # 날짜
    description = Column(String(200))                       # 상세 설명
