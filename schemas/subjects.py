from pydantic import BaseModel
from typing import Optional

# ✅ 입력용: POST 요청에서 사용할 스키마
class SubjectCreate(BaseModel):
    name: str                                # 과목 이름
    category: Optional[str] = None           # 과목 분류 (예: 기본, 예체능, 생활 등)

# ✅ 출력용: GET, POST 응답 등에서 사용할 스키마
class Subject(BaseModel):
    id: int                                  # 고유 과목 ID
    name: str                                # 과목 이름
    category: Optional[str] = None           # 과목 분류

    class Config:
        from_attributes = True               # orm_mode → 최신 Pydantic 문법
