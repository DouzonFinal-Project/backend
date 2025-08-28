from sqlalchemy import Column, Integer, String, Date
from database.db import Base

class Report(Base):
    __tablename__ = "reports"  # 개별 상담/생활지도 보고서 테이블

    id = Column(Integer, primary_key=True, index=True)   # 보고서 고유 ID (Primary Key)
    student_id = Column(Integer, nullable=False)         # 학생 ID (students 테이블과 연동)
    date = Column(Date, nullable=False)                  # 상담/지도 일자
    type = Column(String(50))                            # 보고서 유형 (예: 상담, 지도, 경고)
    content_raw = Column(String(1000))                   # 원본 상담/지도 내용
    summary = Column(String(1000))                       # 요약된 상담 내용 (LLM 또는 수작업 요약)
    emotion = Column(String(50))                         # 감정 태그 (예: 불안, 우울, 분노 등)
