from pydantic import BaseModel
from typing import Optional

class Student(BaseModel):
    id: int                                  # 고유 학생 ID
    student_name: str                        # 학생 이름
    class_id: int                            # 소속 반 ID
    gender: Optional[str] = None             # 성별
    phone: Optional[str] = None              # 연락처
    address: Optional[str] = None            # 주소

    class Config:
        orm_mode = True
