from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import student_info
from routers import student_attendance
from routers import grades
from routers import events
from routers import reports
from routers import school_report

# 🔽 DB 관련 import
from database.db import Base, engine
from models.student_info import StudentInfo  # 최소 하나라도 import 해야 테이블 생성됨

# ✅ FastAPI 인스턴스 생성
app = FastAPI()

# ✅ CORS 설정
origins = [
    "http://localhost:3000",   # 로컬 프론트 주소
    "http://127.0.0.1:3000",   # 로컬host IP
    # "https://your-deployed-frontend.com"  # 배포 시 프론트 주소 추가 가능
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # 모든 origin 허용 시 ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 테이블 생성 (초기 1회 실행)
Base.metadata.create_all(bind=engine)

# ✅ 라우터 연결
app.include_router(student_info.router, prefix="/api")
app.include_router(student_attendance.router, prefix="/api")
app.include_router(grades.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(school_report.router, prefix="/api")

# ✅ 기본 엔드포인트
@app.get("/")
def read_root():
    return {"message": "Welcome to Douzone Final Project"}
