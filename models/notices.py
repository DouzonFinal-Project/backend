from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from database.db import Base

class Notice(Base):
    __tablename__ = "notices"  # 공지사항 테이블

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # 공지 고유 ID
    title = Column(String(100), nullable=False)                             # 공지 제목
    content = Column(String(500), nullable=False)                           # 공지 내용
    target_class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)  # 대상 학급 ID
    date = Column(Date, nullable=False)                                     # 작성일자
    is_important = Column(Boolean, default=False, nullable=False)           # 중요 여부