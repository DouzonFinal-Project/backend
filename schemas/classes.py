from pydantic import BaseModel

# ✅ 응답(Response) / 조회(Read) 용 스키마
# DB에서 불러온 학급 데이터를 API 응답으로 내려줄 때 사용
class Class(BaseModel):
    id: int                          # 학급 고유 ID (PK)
    grade: int                       # 학년
    class_num: int                   # 반 번호
    teacher_id: int                  # 담임 교사 ID (FK)

    class Config:
        # Pydantic v2에서는 orm_mode 대신 from_attributes 사용
        from_attributes = True       


# ✅ 생성(Create) 요청용 스키마
# 새 학급을 추가할 때 요청 바디에 사용
# → id는 DB에서 자동 생성되므로 제외
class ClassCreate(BaseModel):
    grade: int                       # 학년
    class_num: int                   # 반 번호
    teacher_id: int                  # 담임 교사 ID
