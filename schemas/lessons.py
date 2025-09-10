from pydantic import BaseModel
from typing import Optional
from datetime import date

class Lesson(BaseModel):
    id: Optional[int] = None                     # 수업 고유 ID (생성 시 None 허용)
    subject_name: str                            # 과목명
    lesson_title: str                            # 수업 제목
    lesson_content: str                          # 수업 내용
    lesson_time: str                             # 수업 시간
    start_time: str                              # 시작 시간
    end_time: str                                # 종료 시간
    date: Optional[date] = None                  # 날짜 (NULL 가능)
    ppt_link: Optional[str] = None               # PPT 링크 (NULL 가능)

    class Config:
        from_attributes = True
