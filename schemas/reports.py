from pydantic import BaseModel
from typing import Optional
from datetime import date

class Report(BaseModel):
    id: int                                  # 보고서 ID
    student_id: int                          # 학생 ID
    date: date                               # 상담 날짜
    type: Optional[str] = None               # 유형 (상담/지도 등)
    content_raw: Optional[str] = None        # 원본 내용
    summary: Optional[str] = None            # 요약 내용
    emotion: Optional[str] = None            # 감정 태그

    class Config:
        orm_mode = True
