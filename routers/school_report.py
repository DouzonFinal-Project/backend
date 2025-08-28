from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.school_report import SchoolReport as SchoolReportModel
from models.students import Student as StudentModel   # ✅ 학생 테이블 import
from schemas.school_report import SchoolReport as SchoolReportSchema
from typing import List

router = APIRouter(prefix="/school_report", tags=["생활기록부"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================
# [1단계] CRUD 기본 라우터
# ==========================================================

# ✅ [CREATE] 생활기록 추가
@router.post("/")
def create_school_report(report: SchoolReportSchema, db: Session = Depends(get_db)):
    db_report = SchoolReportModel(**report.model_dump())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return {
        "success": True,
        "data": {
            "id": db_report.id,
            "student_id": db_report.student_id,
            "year": db_report.year,
            "semester": db_report.semester,
            "behavior_summary": db_report.behavior_summary,
            "peer_relation": db_report.peer_relation,
            "career_aspiration": db_report.career_aspiration,
            "teacher_feedback": db_report.teacher_feedback
        },
        "message": "생활기록이 성공적으로 추가되었습니다"
    }


# ✅ [READ] 전체 생활기록 조회
@router.get("/")
def read_school_reports(db: Session = Depends(get_db)):
    records = db.query(SchoolReportModel).all()
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "student_id": r.student_id,
                "year": r.year,
                "semester": r.semester,
                "behavior_summary": r.behavior_summary,
                "peer_relation": r.peer_relation,
                "career_aspiration": r.career_aspiration,
                "teacher_feedback": r.teacher_feedback
            }
            for r in records
        ],
        "message": "전체 생활기록 조회 완료"
    }


# ==========================================================
# [2단계] 혼합 라우터
# ==========================================================

# ✅ [READ] 특정 학생 생활기록부
@router.get("/student/{student_id}")
def get_student_school_report(student_id: int, db: Session = Depends(get_db)):
    reports = db.query(SchoolReportModel).filter(SchoolReportModel.student_id == student_id).all()
    if not reports:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 학생의 생활기록부가 없습니다"}
        }
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "student_id": r.student_id,
                "year": r.year,
                "semester": r.semester,
                "behavior_summary": r.behavior_summary,
                "peer_relation": r.peer_relation,
                "career_aspiration": r.career_aspiration,
                "teacher_feedback": r.teacher_feedback
            }
            for r in reports
        ],
        "message": f"학생 ID {student_id} 생활기록 조회 성공"
    }


# ✅ [READ] 특정 반(class_id)의 생활기록부 목록 (조인 기반)
@router.get("/class/{class_id}")
def get_class_school_reports(class_id: int, db: Session = Depends(get_db)):
    reports = (
        db.query(SchoolReportModel)
        .join(StudentModel, StudentModel.id == SchoolReportModel.student_id)
        .filter(StudentModel.class_id == class_id)
        .all()
    )
    if not reports:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 반의 생활기록부가 없습니다"}
        }
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "student_id": r.student_id,
                "year": r.year,
                "semester": r.semester,
                "behavior_summary": r.behavior_summary,
                "peer_relation": r.peer_relation,
                "career_aspiration": r.career_aspiration,
                "teacher_feedback": r.teacher_feedback
            }
            for r in reports
        ],
        "message": f"반 ID {class_id} 생활기록 조회 성공"
    }


# ==========================================================
# [2.5단계] 통합 라우터 (출결 + 성적 + 생활기록부)
# ==========================================================

@router.get("/full/{student_id}")
def get_full_school_report(student_id: int, db: Session = Depends(get_db)):
    """
    특정 학생의 출결 + 성적 + 생활기록부 코멘트 통합 조회
    """
    from models.attendance import Attendance as AttendanceModel
    from models.grades import Grade as GradeModel

    # 출결 조회
    attendance = db.query(AttendanceModel).filter(AttendanceModel.student_id == student_id).all()
    attendance_data = [{"date": a.date, "status": a.status} for a in attendance] if attendance else []

    # 성적 조회
    grades = db.query(GradeModel).filter(GradeModel.student_id == student_id).all()
    grade_data = [
        {"subject": g.subject, "score": g.score, "grade_letter": g.grade_letter}
        for g in grades
    ] if grades else []

    # 생활기록부 조회
    reports = db.query(SchoolReportModel).filter(SchoolReportModel.student_id == student_id).all()
    report_data = [
        {
            "year": r.year,
            "semester": r.semester,
            "behavior_summary": r.behavior_summary,
            "peer_relation": r.peer_relation,
            "career_aspiration": r.career_aspiration,
            "teacher_feedback": r.teacher_feedback
        }
        for r in reports
    ] if reports else []

    return {
        "success": True,
        "student_id": student_id,
        "attendance": attendance_data,
        "grades": grade_data,
        "reports": report_data,
        "message": f"학생 ID {student_id} 생활기록부 통합 조회 성공"
    }


# ==========================================================
# [3단계] Export/Action 라우터
# ==========================================================

# ✅ [EXPORT] 생활기록부 PDF 출력
@router.get("/{report_id}/export/pdf")
def export_school_report_pdf(report_id: int):
    return {
        "success": True,
        "data": {"report_id": report_id},
        "message": f"생활기록 {report_id} PDF 출력 완료"
    }


# ✅ [SEND] 생활기록부 이메일 발송
@router.post("/{report_id}/send-email")
def send_school_report_email(report_id: int, email: str):
    return {
        "success": True,
        "data": {"report_id": report_id, "recipient": email},
        "message": f"생활기록 {report_id}가 {email}로 발송되었습니다"
    }


# ==========================================================
# [4단계] 완전 동적 라우터
# ==========================================================

# ✅ [READ] 생활기록 상세 조회
@router.get("/{report_id}")
def read_school_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(SchoolReportModel).filter(SchoolReportModel.id == report_id).first()
    if report is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "생활기록을 찾을 수 없습니다"}
        }
    return {
        "success": True,
        "data": {
            "id": report.id,
            "student_id": report.student_id,
            "year": report.year,
            "semester": report.semester,
            "behavior_summary": report.behavior_summary,
            "peer_relation": report.peer_relation,
            "career_aspiration": report.career_aspiration,
            "teacher_feedback": report.teacher_feedback
        },
        "message": "생활기록 상세 조회 성공"
    }


# ✅ [UPDATE] 생활기록 수정
@router.put("/{report_id}")
def update_school_report(report_id: int, updated: SchoolReportSchema, db: Session = Depends(get_db)):
    report = db.query(SchoolReportModel).filter(SchoolReportModel.id == report_id).first()
    if report is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "생활기록을 찾을 수 없습니다"}
        }

    for key, value in updated.model_dump().items():
        setattr(report, key, value)

    db.commit()
    db.refresh(report)
    return {
        "success": True,
        "data": {
            "id": report.id,
            "student_id": report.student_id,
            "year": report.year,
            "semester": report.semester,
            "behavior_summary": report.behavior_summary,
            "peer_relation": report.peer_relation,
            "career_aspiration": report.career_aspiration,
            "teacher_feedback": report.teacher_feedback
        },
        "message": "생활기록이 성공적으로 수정되었습니다"
    }


# ✅ [DELETE] 생활기록 삭제
@router.delete("/{report_id}")
def delete_school_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(SchoolReportModel).filter(SchoolReportModel.id == report_id).first()
    if report is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "생활기록을 찾을 수 없습니다"}
        }

    db.delete(report)
    db.commit()
    return {
        "success": True,
        "data": {"report_id": report_id},
        "message": "생활기록이 성공적으로 삭제되었습니다"
    }
