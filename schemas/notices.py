from pydantic import BaseModel
from typing import Optional
from datetime import date

class Notice(BaseModel):
    id: int                                  # 공지 고유 ID
    title: str                               # 제목
    content: str                             # 내용
    target_class_id: int                     # 대상 학급 ID
    date: date                               # 작성일자

    class Config:
        orm_mode = True
