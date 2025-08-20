from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ 미들웨어 임포트
from middlewares.timing import TimingMiddleware
from middlewares.error_handler import add_error_handlers

# ✅ 라우터 임포트
from routers import (
    attendance, auth, classes, events, grades,
    llm,  # ← Gemini API 호출 라우터
    ai_chatbot,  # ← AI 챗봇 라우터
    meetings, notices, reports, school_report,
    students, subjects, teachers, test_scores, tests,
    front_proxy, pdf_reports
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

# ✅ 요청 지연 측정 미들웨어 (응답 헤더 X-Latency-Ms 추가)
app.add_middleware(TimingMiddleware)

# ✅ 전역 에러 핸들러 등록 (일관된 JSON 에러 포맷)
add_error_handlers(app)

# ✅ /v1 프리픽스 라우터 등록
app.include_router(attendance.router,     prefix="/v1")
app.include_router(auth.router,           prefix="/v1")
app.include_router(classes.router,        prefix="/v1")
app.include_router(events.router,         prefix="/v1")
app.include_router(grades.router,         prefix="/v1")
app.include_router(llm.router,            prefix="/v1")   # ✅ 새 Gemini 라우터
app.include_router(meetings.router,       prefix="/v1")
app.include_router(notices.router,        prefix="/v1")
app.include_router(reports.router,        prefix="/v1")
app.include_router(school_report.router,  prefix="/v1")
app.include_router(students.router,       prefix="/v1")
app.include_router(subjects.router,       prefix="/v1")
app.include_router(teachers.router,       prefix="/v1")
app.include_router(test_scores.router,    prefix="/v1")
app.include_router(tests.router,          prefix="/v1")
app.include_router(front_proxy.router,    prefix="/v1")
app.include_router(ai_chatbot.router,     prefix="/v1")   # ✅ 새 AI 통합 라우터          
app.include_router(pdf_reports.router,    prefix="/v1")   # ✅ PDF 생성 라우터

# ✅ 헬스체크 엔드포인트
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}

# ✅ 루트 엔드포인트
@app.get("/")
def root():
    return {"message": "Teacher Assistant API - 초등학교 교사 행정지원 AI"}
