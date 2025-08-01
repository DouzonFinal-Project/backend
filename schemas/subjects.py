from pydantic import BaseModel
from typing import Optional

class Subject(BaseModel):
    id: int                                  # 과목 고유 ID
    name: str                                # 과목 이름
    category: Optional[str] = None           # 과목 분류 (필수/선택 등)

    class Config:
        orm_mode = True
