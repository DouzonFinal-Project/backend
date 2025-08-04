from pydantic import BaseModel
from typing import Optional
from schemas.students import Student        # 학생 관계 스키마
from schemas.teachers import Teacher        # 교사 관계 스키마

# ✅ 입력용 스키마: 상담 기록 생성/수정 시 사용 (POST, PUT)
class MeetingCreate(BaseModel):
    title: str                               # 상담 제목
    meeting_type: Optional[str] = None       # 상담 유형 (예: 생활, 학업, 진로 등)
    student_id: Optional[int] = None         # 상담 대상 학생 ID (외래키, 선택적으로 허용)
    teacher_id: Optional[int] = None         # 상담 진행 교사 ID (외래키, 선택적으로 허용)

# ✅ 출력용 스키마: 상담 기록 조회 시 사용 (GET 응답)
class Meeting(MeetingCreate):
    id: int                                  # 상담 고유 ID (Primary Key)
    student: Optional[Student] = None        # 연관된 학생 정보 (전체 조회용)
    teacher: Optional[Teacher] = None        # 연관된 교사 정보 (전체 조회용)

    class Config:
        from_attributes = True               # SQLAlchemy 모델로부터 자동 변환 허용 (Pydantic v2 기준)
