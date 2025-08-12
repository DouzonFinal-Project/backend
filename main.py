from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ 라우터 임포트
from routers import (
    attendance, auth, classes, events, grades, llm, meetings,
    notices, reports, school_report, students, subjects, teachers,
    test_scores, tests
)

app = FastAPI(
    title="Teacher Assistant API",
    description="초등학교 교사 행정지원 AI 챗봇 백엔드 API",
    version="1.0.0"
)

# ✅ CORS 설정 (프론트엔드 연동 대비)
origins = [
    "http://localhost:3000",  # 로컬 개발용 React/Next.js
    # 추후 배포 도메인 추가 가능
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ /v1 프리픽스 라우터 등록
app.include_router(attendance.router, prefix="/v1/attendance")
app.include_router(auth.router, prefix="/v1/auth")
app.include_router(classes.router, prefix="/v1/classes")
app.include_router(events.router, prefix="/v1/events")
app.include_router(grades.router, prefix="/v1/grades")
app.include_router(llm.router, prefix="/v1/llm")
app.include_router(meetings.router, prefix="/v1/meetings")
app.include_router(notices.router, prefix="/v1/notices")
app.include_router(reports.router, prefix="/v1/reports")
app.include_router(school_report.router, prefix="/v1/school-report")
app.include_router(students.router, prefix="/v1/students")
app.include_router(subjects.router, prefix="/v1/subjects")
app.include_router(teachers.router, prefix="/v1/teachers")
app.include_router(test_scores.router, prefix="/v1/test-scores")
app.include_router(tests.router, prefix="/v1/tests")

# ✅ 헬스체크 엔드포인트
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}

# ✅ 루트 엔드포인트
@app.get("/")
def root():
    return {"message": "Teacher Assistant API - 초등학교 교사 행정지원 AI"}
