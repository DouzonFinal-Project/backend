from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from collections import Counter

from database.db import SessionLocal
from models.attendance import Attendance as AttendanceModel
from models.students import Student as StudentModel

router = APIRouter(prefix="/attendance/dashboard", tags=["출결 대시보드"])

# ✅ 공통 DB 세션
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ 상태 매핑 (한글 → 영문)
STATUS_MAP = {
    "출석": "present",
    "결석": "absent",
    "지각": "late",
    "조퇴": "early_leave"
}
def convert_status(status: str) -> str:
    return STATUS_MAP.get(status, status)


# ==========================================================
# [DASHBOARD] 반별 출결 대시보드 조회
# 프론트 대시보드(출결 현황, 주의 학생, 처리현황, 상세현황, 주간요약) 한 번에 반환
# ==========================================================
@router.get("/{class_id}")
def get_attendance_dashboard(
    class_id: int,
    date: str = Query(..., description="조회 날짜 (예: 2025-07-26)"),
    db: Session = Depends(get_db),
):
    target_date = datetime.strptime(date, "%Y-%m-%d").date()

    # 1) 당일 출결 데이터
    records = (
        db.query(AttendanceModel, StudentModel)
        .join(StudentModel, AttendanceModel.student_id == StudentModel.id)
        .filter(StudentModel.class_id == class_id)
        .filter(AttendanceModel.date == target_date)
        .all()
    )

    total_students = len(records)
    status_counter = Counter([r.Attendance.status for r in records])

    present = status_counter.get("출석", 0)
    absent = status_counter.get("결석", 0)
    late = status_counter.get("지각", 0)
    early_leave = status_counter.get("조퇴", 0)
    rate = round((present / total_students) * 100, 1) if total_students else 0

    # 2) 주의 필요 학생 (연속 결석 or 특정 사유 다수)
    need_attention = []
    for att, stu in records:
        if att.status == "결석":
            # 예시: 최근 3일 연속 결석 여부 확인
            past_records = (
                db.query(AttendanceModel)
                .filter(AttendanceModel.student_id == stu.id)
                .filter(AttendanceModel.date.between(target_date - timedelta(days=3), target_date))
                .all()
            )
            if all(r.status == "결석" for r in past_records) and len(past_records) == 3:
                need_attention.append({"name": stu.student_name, "issue": "연속 결석 위험"})
        if att.reason and att.reason.count(",") >= 2:
            need_attention.append({"name": stu.student_name, "issue": "특별 사유 다수"})

    # 3) 처리 현황 (예: 결석계 제출, 무단결석)
    processed_absent = sum(1 for att, _ in records if att.status == "결석" and "병결" in (att.reason or ""))
    unreported_absent = sum(1 for att, _ in records if att.status == "결석" and "무단" in (att.reason or ""))

    # 4) 당일 상세 현황
    details = [
        {
            "student_name": stu.student_name,
            "status": convert_status(att.status),
            "reason": att.reason,
            "note": "연속결석 위험" if {"name": stu.student_name, "issue": "연속 결석 위험"} in need_attention else ""
        }
        for att, stu in records
    ]

    # 5) 주간 요약 (최근 5일치 출석률 + 결석 사유 분석)
    start_week = target_date - timedelta(days=4)
    week_records = (
        db.query(AttendanceModel, StudentModel)
        .join(StudentModel, AttendanceModel.student_id == StudentModel.id)
        .filter(StudentModel.class_id == class_id)
        .filter(AttendanceModel.date.between(start_week, target_date))
        .all()
    )

    grouped = {}
    for att, stu in week_records:
        grouped.setdefault(att.date, []).append(att)

    total_days = len(grouped)
    total_rate = 0
    for day_records in grouped.values():
        d_total = len(day_records)
        d_present = sum(1 for r in day_records if r.status == "출석")
        total_rate += (d_present / d_total * 100) if d_total else 0

    avg_rate = round(total_rate / total_days, 1) if total_days else 0

    # 결석 사유 분석
    reasons = [r.reason for r, _ in week_records if r.status == "결석" and r.reason]
    reason_counter = Counter(reasons)
    top_reason = reason_counter.most_common(1)[0] if reason_counter else ("None", 0)

    # ======================================================
    # 최종 응답
    # ======================================================
    return {
        "success": True,
        "data": {
            "class_id": class_id,
            "date": str(target_date),
            "overview": {
                "total": total_students,
                "present": present,
                "absent": absent,
                "late": late,
                "early_leave": early_leave,
                "attendance_rate": f"{rate}%"
            },
            "alerts": {
                "need_attention": need_attention
            },
            "processing": {
                "absence_report_submitted": processed_absent,
                "unreported_absent": unreported_absent
            },
            "details": details,
            "weekly_summary": {
                "period": f"{start_week} ~ {target_date}",
                "avg_attendance_rate": f"{avg_rate}%",
                "top_absent_reason": top_reason[0],
                "top_absent_rate": f"{round((top_reason[1] / len(reasons)) * 100, 1)}%" if reasons else "0%"
            }
        },
        "message": f"{class_id}반 출결 대시보드 조회 성공"
    }
