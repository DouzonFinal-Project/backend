from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from collections import Counter

from database.db import SessionLocal
from models.attendance import Attendance as AttendanceModel
from models.students import Student as StudentModel   # ✅ 학급(class_id) 참조용
from schemas.attendance import Attendance as AttendanceSchema

router = APIRouter(prefix="/attendance", tags=["attendance"])

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
# [1단계] CRUD 기본 라우터
# ==========================================================

# ✅ [CREATE] 출석 기록 추가
@router.post("/")
def create_attendance(attendance: AttendanceSchema, db: Session = Depends(get_db)):
    db_attendance = AttendanceModel(**attendance.model_dump())
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return {
        "success": True,
        "data": {
            "id": db_attendance.id,
            "student_id": db_attendance.student_id,
            "date": str(db_attendance.date),
            "status": db_attendance.status,
            "reason": db_attendance.reason,
        },
        "message": "Attendance record created successfully"
    }

# ✅ [READ] 전체 출석 기록 조회
@router.get("/")
def read_attendance_list(db: Session = Depends(get_db)):
    records = db.query(AttendanceModel).all()
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "student_id": r.student_id,
                "date": str(r.date),
                "status": r.status,
                "reason": r.reason,
            }
            for r in records
        ]
    }

# ==========================================================
# [2단계] 정적 요약 라우터
# ==========================================================

# ✅ [DAILY SUMMARY] 특정 날짜 출석 현황
@router.get("/daily-summary")
def get_daily_attendance_summary(
    date: str = Query(..., description="조회할 날짜 (예: 2025-09-17)"),
    db: Session = Depends(get_db),
):
    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    records = db.query(AttendanceModel).filter(AttendanceModel.date == target_date).all()

    total = len(records)
    status_counter = Counter([r.status for r in records])

    present = status_counter.get("출석", 0)
    absent = status_counter.get("결석", 0)
    late = status_counter.get("지각", 0)
    checkin = status_counter.get("조퇴", 0)

    rate = round((present / total) * 100, 1) if total else 0

    return {
        "success": True,
        "data": {
            "date": date,
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "checkin": checkin,
            "attendance_rate": f"{rate}%"
        }
    }

# ✅ [WEEKLY SUMMARY] 특정 주간 출석 현황
@router.get("/weekly-summary")
def get_weekly_attendance_summary(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
):
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    records = db.query(AttendanceModel).filter(AttendanceModel.date.between(start, end)).all()

    grouped = {}
    for r in records:
        grouped.setdefault(r.date, []).append(r)

    total_days = len(grouped)
    total_rate = 0
    for day_records in grouped.values():
        day_total = len(day_records)
        day_present = sum(1 for r in day_records if r.status == "출석")
        total_rate += (day_present / day_total * 100) if day_total else 0

    avg_rate = round(total_rate / total_days, 1) if total_days else 0

    reasons = [r.reason for r in records if r.status == "결석" and r.reason]
    reason_counter = Counter(reasons)
    top_reason = reason_counter.most_common(1)[0] if reason_counter else ("None", 0)

    return {
        "success": True,
        "data": {
            "period": f"{start_date} ~ {end_date}",
            "total_records": len(records),
            "average_attendance_rate": f"{avg_rate}%",
            "top_absent_reason": top_reason[0],
            "top_absent_rate": f"{round((top_reason[1] / len(reasons)) * 100, 1)}%" if reasons else "0%",
            "total_absent": len(reasons),
        }
    }

# ✅ [MONTHLY SUMMARY] 특정 반 월간 출석 현황
@router.get("/monthly-summary")
def get_monthly_attendance_summary(
    class_id: int,
    month: str,
    db: Session = Depends(get_db),
):
    year, mon = map(int, month.split("-"))
    records = (
        db.query(AttendanceModel)
        .join(StudentModel, AttendanceModel.student_id == StudentModel.id)
        .filter(StudentModel.class_id == class_id)
        .filter(func.year(AttendanceModel.date) == year)
        .filter(func.month(AttendanceModel.date) == mon)
        .all()
    )

    total = len(records)
    present = sum(1 for r in records if r.status == "출석")
    absent = sum(1 for r in records if r.status == "결석")
    late = sum(1 for r in records if r.status == "지각")
    rate = round((present / total) * 100, 1) if total else 0

    return {
        "success": True,
        "data": {
            "class_id": class_id,
            "month": month,
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "attendance_rate": f"{rate}%"
        }
    }

# ==========================================================
# [3단계] 혼합 요약 라우터
# ==========================================================

# ✅ [STUDENT SUMMARY] 특정 학생 누적 출석 현황
@router.get("/student/{student_id}/summary")
def get_student_attendance_summary(student_id: int, db: Session = Depends(get_db)):
    records = db.query(AttendanceModel).filter(AttendanceModel.student_id == student_id).all()
    if not records:
        return {"success": False, "error": {"code": 404, "message": "Attendance records not found for student"}}

    total = len(records)
    present = sum(1 for r in records if r.status == "출석")
    absent = sum(1 for r in records if r.status == "결석")
    late = sum(1 for r in records if r.status == "지각")
    rate = round((present / total) * 100, 1) if total else 0

    return {
        "success": True,
        "data": {
            "student_id": student_id,
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "attendance_rate": f"{rate}%"
        }
    }

# ✅ [CLASS SUMMARY] 특정 반 오늘 출석 현황
@router.get("/class/{class_id}/summary")
def get_class_attendance_summary(class_id: int, db: Session = Depends(get_db)):
    records = (
        db.query(AttendanceModel)
        .join(StudentModel, AttendanceModel.student_id == StudentModel.id)
        .filter(StudentModel.class_id == class_id)
        .filter(AttendanceModel.date == date.today())  # ✅ 오늘 날짜만
        .all()
    )
    if not records:
        return {"success": False, "error": {"code": 404, "message": "오늘 출석 기록이 없습니다."}}

    from models.classes import Class as ClassModel
    class_info = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    class_label = f"{class_info.grade}학년 {class_info.class_num}반" if class_info else f"Class {class_id}"

    total = len(records)
    present = sum(1 for r in records if r.status == "출석")
    absent = sum(1 for r in records if r.status == "결석")
    late = sum(1 for r in records if r.status == "지각")
    rate = round((present / total) * 100, 1) if total else 0

    return {
        "success": True,
        "data": {
            "class_id": class_id,
            "class_label": class_label,
            "date": str(date.today()),
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "attendance_rate": f"{rate}%"
        }
    }

# ==========================================================
# [4단계] 동적 라우터
# ==========================================================

# ✅ [READ] 출석 단일 기록 조회
@router.get("/{attendance_id}")
def read_attendance(attendance_id: int, db: Session = Depends(get_db)):
    attendance = db.query(AttendanceModel).filter(AttendanceModel.id == attendance_id).first()
    if not attendance:
        return {"success": False, "error": {"code": 404, "message": "Attendance record not found"}}
    return {
        "success": True,
        "data": {
            "id": attendance.id,
            "student_id": attendance.student_id,
            "date": str(attendance.date),
            "status": attendance.status,
            "reason": attendance.reason,
        }
    }

# ✅ [UPDATE] 출석 기록 수정
@router.put("/{attendance_id}")
def update_attendance(attendance_id: int, updated: AttendanceSchema, db: Session = Depends(get_db)):
    attendance = db.query(AttendanceModel).filter(AttendanceModel.id == attendance_id).first()
    if not attendance:
        return {"success": False, "error": {"code": 404, "message": "Attendance record not found"}}

    for key, value in updated.model_dump().items():
        setattr(attendance, key, value)

    db.commit()
    db.refresh(attendance)
    return {
        "success": True,
        "data": {
            "id": attendance.id,
            "student_id": attendance.student_id,
            "date": str(attendance.date),
            "status": attendance.status,
            "reason": attendance.reason,
        },
        "message": "Attendance record updated successfully"
    }

# ✅ [DELETE] 출석 기록 삭제
@router.delete("/{attendance_id}")
def delete_attendance(attendance_id: int, db: Session = Depends(get_db)):
    attendance = db.query(AttendanceModel).filter(AttendanceModel.id == attendance_id).first()
    if not attendance:
        return {"success": False, "error": {"code": 404, "message": "Attendance record not found"}}

    db.delete(attendance)
    db.commit()
    return {
        "success": True,
        "data": {
            "attendance_id": attendance_id,
        },
        "message": "Attendance record deleted successfully"
    }

# ==========================================================
# [5단계] 확장 통계 라우터
# ==========================================================

# ✅ [STATS] 학생별 출석 통계 조회 (전체 기간)
@router.get("/stats/students")
async def get_student_attendance_stats(db: Session = Depends(get_db)):
    try:
        students = db.query(StudentModel).all()
        stats_data = []

        for student in students:
            attendance_counts = db.query(
                AttendanceModel.status,
                func.count(AttendanceModel.id).label("count")
            ).filter(
                AttendanceModel.student_id == student.id
            ).group_by(AttendanceModel.status).all()

            status_counts = {status: count for status, count in attendance_counts}

            stats_data.append({
                "student_id": student.id,
                "student_name": student.student_name,
                "class_id": student.class_id,
                "absent_count": status_counts.get("결석", 0),
                "late_count": status_counts.get("지각", 0),
                "early_count": status_counts.get("조퇴", 0),
                "present_count": status_counts.get("출석", 0),
            })

        return {"success": True, "data": stats_data}

    except Exception as e:
        return {"success": False, "error": f"학생별 출석 통계 조회 실패: {str(e)}"}
