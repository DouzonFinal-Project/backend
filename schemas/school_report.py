from pydantic import BaseModel

# ✅ 입력용 스키마 (POST 요청 시 사용)
class SchoolReportCreate(BaseModel):
    student_id: int                   # 학생 고유 ID
    student_name: str                # 학생 이름
    behavior_summary: str | None = None      # 생활 태도 요약
    career_aspiration: str | None = None     # 진로 희망
    teacher_feedback: str | None = None      # 교사 종합 의견

# ✅ 응답용 스키마 (GET 응답 시 사용)
class SchoolReport(BaseModel):
    report_id: int                   # 보고서 고유 ID (DB에서 자동 생성)
    student_id: int
    student_name: str
    behavior_summary: str | None = None
    career_aspiration: str | None = None
    teacher_feedback: str | None = None

    class Config:
        orm_mode = True             # SQLAlchemy 모델과 호환 설정
