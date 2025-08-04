from pydantic import BaseModel
from typing import Optional

# ✅ 입력용 (POST/PUT 등)
class StudentCreate(BaseModel):
    student_name: str                        # 학생 이름
    class_id: int                            # 소속 반 ID
    gender: Optional[str] = None             # 성별
    phone: Optional[str] = None              # 연락처
    address: Optional[str] = None            # 주소

# ✅ 전체 출력용 (GET, 상세조회 등)
class Student(StudentCreate):
    id: int

    class Config:
        from_attributes = True  # Pydantic v2 기준
