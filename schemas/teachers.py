from pydantic import BaseModel
from typing import Optional

# ✅ 입력용 스키마: 교사 정보를 새로 생성할 때 사용 (POST 요청 등)
class TeacherCreate(BaseModel):
    name: str                                # 교사 이름
    email: Optional[str] = None              # 이메일 주소
    phone: Optional[str] = None              # 연락처
    subject: Optional[str] = None            # 담당 과목 이름

# ✅ 출력용 스키마: 교사 정보를 조회할 때 사용 (GET 응답 등)
class Teacher(TeacherCreate):
    id: int                                  # 고유 교사 ID

    class Config:
        from_attributes = True              # SQLAlchemy 모델에서 Pydantic 객체로 변환 허용
