from pydantic import BaseModel
from typing import Optional
from datetime import date

class Test(BaseModel):
    id: int                                  # 시험 ID
    subject_id: int                          # 과목 ID
    test_name: str                           # 시험 이름
    test_date: date                          # 시험 날짜
    class_id: int                            # 대상 학급 ID
    subject_name: Optional[str] = None       # 과목 이름 (중복 저장용)

    class Config:
        orm_mode = True
