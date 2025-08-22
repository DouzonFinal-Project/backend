from pydantic import BaseModel
from typing import Optional
from datetime import date

# ✅ 조회/응답용 스키마
class Test(BaseModel):
    id: int                                  # 시험 ID (PK)
    subject_id: int                          # 과목 ID (FK)
    test_name: str                           # 시험 이름
    test_date: date                          # 시험 날짜
    class_id: int                            # 대상 학급 ID
    subject_name: Optional[str] = None       # 과목 이름 (조인/중복 저장용)

    class Config:
        from_attributes = True               # ⚠️ Pydantic v2 대응


# ✅ 생성(Create) 전용 스키마
# → id, subject_name은 제외 (DB에서 자동 생성되거나 join으로 얻을 수 있음)
class TestCreate(BaseModel):
    subject_id: int                          # 과목 ID
    test_name: str                           # 시험 이름
    test_date: date                          # 시험 날짜
    class_id: int                            # 대상 학급 ID
