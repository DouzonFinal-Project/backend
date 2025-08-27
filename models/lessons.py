from sqlalchemy import Column, Integer, String, Date
from database.db import Base

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)           # 수업 고유 ID (Primary Key)
    subject_name = Column(String(50), nullable=False)           # 과목명 (수학, 국어, 영어)
    lesson_title = Column(String(100), nullable=False)          # 수업 제목
    lesson_content = Column(String(200), nullable=False)        # 진도 내용
    lesson_time = Column(String(20), nullable=False)            # 교시 (1교시, 2교시 등)
    start_time = Column(String(10), nullable=False)             # 시작 시간 (09:00)
    end_time = Column(String(10), nullable=False)               # 종료 시간 (10:00)
    date = Column(Date, nullable=True)                          # 특정 날짜 (선택사항)
    ppt_link = Column(String(500), nullable=True)               # PPT 링크 