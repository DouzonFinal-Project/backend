from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class Report(Base):
    __tablename__ = "reports"  # 개별 상담/생활지도 보고서 테이블

    id = Column(Integer, primary_key=True, index=True)   # 보고서 고유 ID (Primary Key)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)  # 상담/회의 ID (meetings 테이블과 연동)

    type = Column(String(50))                            # 보고서 유형 (예: 상담, 지도, 경고)
    content_raw = Column(String(1000))                   # 원본 상담/지도 내용
    summary = Column(String(1000))                       # 요약된 상담 내용 (LLM 또는 수작업 요약)
    emotion = Column(String(50))                         # 감정 태그 (예: 불안, 우울, 분노 등)

    # ✅ 관계 설정: Meeting ↔ Report (N:1)
    meeting = relationship("Meeting", back_populates="reports")
