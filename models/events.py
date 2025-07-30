from sqlalchemy import Column, Integer, String, Date
from database.db import Base

class Event(Base):
    __tablename__ = "events"  # 학사일정 테이블

    event_id = Column(Integer, primary_key=True, index=True)      # 고유 ID (자동 증가)
    title = Column(String(200), nullable=False)                   # 일정 제목
    date = Column(Date, nullable=False)                           # 일정 날짜
    location = Column(String(100))                                # 장소
    target = Column(String(100))                                  # 대상 (예: 전교생, 3학년 등)
