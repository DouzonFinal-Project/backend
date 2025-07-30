from pydantic import BaseModel
from datetime import date

# ✅ 출결 등록용 (POST 요청)
class StudentAttendanceCreate(BaseModel):
    student_id: int                  # 학생 고유 ID
    student_name: str               # 학생 이름
    date: date                      # 출결 일자
    status: str                     # 출결 상태 (출석, 결석, 지각 등)
    reason: str                     # 출결 사유

# ✅ 출결 조회/응답용 (GET 응답)
class StudentAttendance(BaseModel):
    id: int                         # 출결 고유 ID (DB에서 자동 생성됨)
    student_id: int
    student_name: str
    date: date
    status: str
    reason: str

    class Config:
        orm_mode = True             # SQLAlchemy 모델 연동 허용
