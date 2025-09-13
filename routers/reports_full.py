from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal

router = APIRouter(prefix="/reports", tags=["보고서 전체 호출"])

# ==========================================================
# [공통] DB 세션 관리
# ==========================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================
# ✅ [OVERVIEW] 보고서 개요 (선택 전 화면)
# ==========================================================
@router.get("/overview")
def get_reports_overview(db: Session = Depends(get_db)):
    """보고서 개요 조회 (마지막 생성 보고서, 총 개수, 선택 옵션)"""
    return {
        "last_report": {"type": "monthly", "date": "2025-07-28"},
        "total_reports": 12,
        "available_types": ["weekly", "monthly", "grades"]
    }


# ==========================================================
# ✅ [WEEKLY] 주간 학급 현황 보고서 전체 호출
# ==========================================================
@router.get("/weekly/full")
def get_weekly_report(class_id: int, start_date: str, end_date: str, db: Session = Depends(get_db)):
    """주간 보고서 전체 호출"""
    return {
        "summary": {
            "total_students": 28,
            "attendance_rate": 96.4,
            "avg_score": 82.3,
            "missing_assignments": 5,
            "counseling": 3,
            "special_notes": 2
        },
        "details": {
            "environment": "출석률 양호, 결석 학생 1명",
            "learning": "평균 점수 82.3, 과제 제출률 90%",
            "counseling": "상담 3건 진행",
            "special_notes": "학부모 연락 필요"
        }
    }


# ==========================================================
# ✅ [MONTHLY] 월간 학사 보고서 전체 호출
# ==========================================================
@router.get("/monthly/full")
def get_monthly_report(class_id: int, month: str, db: Session = Depends(get_db)):
    """월간 보고서 전체 호출"""
    return {
        "summary": {
            "school_days": 22,
            "attendance_rate": 95.7,
            "counseling": 12,
            "incidents": 2,
            "curriculum_progress": 100
        },
        "details": {
            "education": "정규 교육과정 22일 완전 운영",
            "students": "결석 학생 1명, 과제 제출률 95%",
            "parents": "학부모 상담 12건 진행",
            "notes": "안전사고 2건 조치"
        }
    }


# ==========================================================
# ✅ [GRADES] 성적 분석 보고서 전체 호출
# ==========================================================
@router.get("/grades/full")
def get_grades_report(class_id: int, exam_period: str, db: Session = Depends(get_db)):
    """성적 분석 보고서 전체 호출"""
    return {
        "summary": {
            "avg_score": 82.3,
            "max_score": 95,
            "min_score": 68,
            "students_over_80": 21,
            "excellent": 3,
            "grade_A_ratio": "20%"
        },
        "subject_analysis": [
            {"subject": "국어", "avg": 84.2, "max": 95, "min": 72, "remark": "논술형 문제 향상"},
            {"subject": "수학", "avg": 87.5, "max": 92, "min": 68, "remark": "고난도 문항 취약"},
            {"subject": "영어", "avg": 79.8, "max": 92, "min": 65, "remark": "듣기 파트 집중 필요"}
        ],
        "improvement": "수학 고난도 대비 수업 강화 필요"
    }
