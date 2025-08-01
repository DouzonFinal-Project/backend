from pydantic import BaseModel

class Class(BaseModel):
    id: int                          # 학급 고유 ID
    grade: int                       # 학년
    class_num: int                   # 반 번호
    teacher_id: int                  # 담임 교사 ID

    class Config:
        orm_mode = True
