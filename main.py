from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 🔽 2안 기준: 각 기능별 라우터 import
from routers import (
    students,
    teachers,
    classes,
    subjects,
    tests,
    test_scores,
    attendance,
    events,
    reports,
    school_report,
    grades,
    meetings,
    notices,
    auth
)

# 🔽 DB 관련 import
from database.db import Base, engine
from models.students import Student  # ✅ 2안 기준 모델 1개만 임포트 (create_all용)

# ✅ FastAPI 인스턴스 생성
app = FastAPI()

# ✅ CORS 설정
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 테이블 자동 생성
Base.metadata.create_all(bind=engine)

# ✅ 각 라우터 등록 (prefix는 "/api")
app.include_router(students.router, prefix="/api")
app.include_router(teachers.router, prefix="/api")
app.include_router(classes.router, prefix="/api")
app.include_router(subjects.router, prefix="/api")
app.include_router(tests.router, prefix="/api")
app.include_router(test_scores.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(school_report.router, prefix="/api")
app.include_router(grades.router, prefix="/api")
app.include_router(meetings.router, prefix="/api")
app.include_router(notices.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

# ✅ 기본 테스트 엔드포인트
@app.get("/")
def read_root():
    return {"message": "Welcome to Douzone Final Project"}
