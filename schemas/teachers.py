from pydantic import BaseModel
from typing import Optional

class Teacher(BaseModel):
    id: int                                  # 고유 교사 ID
    name: str                                # 교사 이름
    email: Optional[str] = None              # 이메일 주소
    phone: Optional[str] = None              # 연락처
    subject: Optional[str] = None            # 담당 과목 이름

    class Config:
        orm_mode = True
