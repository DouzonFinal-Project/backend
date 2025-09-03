📌 새로운 README.md 초안
# 👩‍🏫 Teacher Assistant AI Chatbot (초등학교 교사 행정지원)

이 프로젝트는 초등학교 교사의 행정 업무를 효율화하기 위한 **AI 기반 행정지원 시스템**입니다.  
FastAPI + MySQL + SQLAlchemy + Milvus + LLM(Gemini/OpenAI) 기반으로 개발되었으며,  
교사의 상담/성적/출결/공지/일정 관리 등을 자동화하고, AI 챗봇과 연동하여 지능형 질의응답을 제공합니다.

---

## 🚀 주요 기능
- **학생 관리**: 학생 기본 정보, 성적, 생활기록부 관리
- **수업/과목 관리**: 과목, 수업(lessons), 시험, 성적 기록
- **상담/보고서**: 상담 기록, 보고서 요약, 감정 태깅
- **출결 관리**: 학생 출석/결석/지각 등 기록
- **일정/공지**: 학교 행사 일정, 공지사항 관리
- **AI 챗봇**: 상담 요약, 성적 질의, 일정 안내 등 LLM 연동
- **PDF 리포트**: 생활기록부/상담보고서 PDF 변환 기능

---

## 📂 프로젝트 구조

### 루트 디렉토리


backend/
┣ .env # 환경변수 설정 (DB 접속정보, API KEY 등)
┣ .gitignore # Git에 올리지 않을 파일/폴더 목록
┣ docker-compose.yml # Docker 서비스 정의 (DB, 백엔드 컨테이너 설정)
┣ Dockerfile # 백엔드 앱을 Docker 이미지로 빌드하기 위한 설정
┣ ERD.png # ERD 다이어그램 이미지 (발표/문서용)
┣ main.py # FastAPI 앱 진입점 (백엔드 실행 시작 파일)
┣ README.md # 프로젝트 소개 문서 (GitHub 기본 표시 문서)
┗ requirements.txt # Python 패키지 의존성 목록 (pip install -r requirements.txt)


### backend 세부 구조


┣ config/ # 설정 (settings.py 등)
┣ database/ # DB 연결 (db.py)
┣ dependencies/ # 공통 의존성 (보안, 인증 등)
┣ middlewares/ # 미들웨어 (logging, error_handler 등)
┣ models/ # 14개 테이블 (students, teachers, classes, subjects,
┃ # tests, test_scores, grades, attendance, events,
┃ # meetings, notices, reports, school_report, lessons)
┣ routers/ # CRUD 라우터 + 확장 라우터 + ai, ai_chatbot, pdf_reports 등
┣ schemas/ # Pydantic 스키마 정의
┣ scripts/ # CSV → DB 마이그레이션 스크립트
┣ services/
┃ ┣ ai_client.py
┃ ┣ ai_service.py
┃ ┣ ai_handlers/ # attendance_handler, event_handler, grade_handler, ...
┃ ┗ llm/ # llm_gemini.py, http_client.py, pdf_service.py 등
┣ templates/ # PDF 변환용 HTML 템플릿
┗ main.py # FastAPI 엔트리포인트


---

## ⚙️ 기술 스택
- **Backend**: FastAPI, SQLAlchemy
- **Database**: MySQL, Milvus(Vector DB)
- **AI/LLM**: Google Gemini / OpenAI GPT
- **Frontend**: React (별도 레포지토리)
- **Infra**: Docker, Cursor, DBeaver
- **기타**: WeasyPrint(PDF 변환)

---

## 🧑‍💻 실행 방법

```bash
# 가상환경 실행 후
uvicorn main:app --reload


Swagger UI: http://localhost:8000/docs

📌 ERD

전체 테이블 14개 (students, teachers, classes, subjects, tests, test_scores, grades, attendance, events, meetings, notices, reports, school_report, lessons)

ERD.png 파일 참고 (발표용 ERD 다이어그램)

🤝 기여

AI 개발: 상담/성적/일정 LLM 핸들러

백엔드 개발: FastAPI, DB 모델링, API 라우터

프론트엔드 개발: React UI 연동

인프라: DB/서버 환경 세팅