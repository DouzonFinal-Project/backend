from pydantic import BaseModel

class StudentInfo(BaseModel):
    student_id: int                  # 학생 고유 ID
    student_name: str               # 학생 이름
    gender: str                     # 성별 (예: 남, 여)
    phone: str                      # 연락처
    address: str                    # 주소

    class Config:
        orm_mode = True             # SQLAlchemy 모델과 호환되도록 설정
