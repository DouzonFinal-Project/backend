from pydantic import BaseModel
from datetime import date
from typing import Optional

# ==========================================================
# [입력용 스키마]
# ==========================================================
class ReportCreate(BaseModel):
    student_id: int                 # 학생 ID
    date: date                      # 상담/지도 일자
    type: Optional[str] = None      # 보고서 유형
    content_raw: Optional[str] = None  # 원본 상담 내용
    summary: Optional[str] = None      # 요약 내용
    emotion: Optional[str] = None      # 감정 태그


# ==========================================================
# [출력용 스키마]
# ==========================================================
class Report(ReportCreate):
    id: int                         # 보고서 고유 ID

    class Config:
        from_attributes = True
