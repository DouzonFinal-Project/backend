from pydantic import BaseModel
from typing import Optional
from datetime import date


# ==========================================================
# [입력용 스키마]
# ==========================================================
class NoticeCreate(BaseModel):
    title: str                               # 제목
    content: str                             # 내용
    target_class_id: int                     # 대상 학급 ID
    date: date                               # 작성일자
    is_important: Optional[bool] = False     # 중요 여부


# ==========================================================
# [출력용 스키마]
# ==========================================================
class Notice(NoticeCreate):
    id: int                                  # 공지 고유 ID

    class Config:
        from_attributes = True               # ✅ Pydantic v2 대응
