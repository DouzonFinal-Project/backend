from sqlalchemy import Column, Integer, String, Date, Time
from database.db import Base

class Event(Base):
    __tablename__ = "events"  # 학사 일정 테이블

    id = Column(Integer, primary_key=True, index=True)      # 일정 고유 ID (Primary Key)
    event_name = Column(String(100), nullable=False)        # 행사/일정 이름 (예: 체육대회)
    event_type = Column(String(50))                         # 일정 유형 (예: 공휴일, 수업, 행사)
    start_date = Column(Date, nullable=False)               # 시작 날짜
    end_date = Column(Date, nullable=True)                  # 종료 날짜 (NULL 가능)
    start_time = Column(Time, nullable=True)                # 시작 시간 (NULL 가능)
    end_time = Column(Time, nullable=True)                  # 종료 시간 (NULL 가능)
    description = Column(String(200))                       # 상세 설명
