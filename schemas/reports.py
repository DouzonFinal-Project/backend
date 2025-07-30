from pydantic import BaseModel
from datetime import date

# ✅ 등록용 (POST)
class ReportCreate(BaseModel):
    student_id: int
    student_name: str
    date: date
    type: str
    teacher_note: str

# ✅ 조회/응답용 (GET/PUT 응답)
class Report(BaseModel):
    report_id: int
    student_id: int
    student_name: str
    date: date
    type: str
    teacher_note: str

    class Config:
        orm_mode = True
