from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from collections import Counter
from typing import List

from database.db import SessionLocal
from models.attendance import Attendance as AttendanceModel
from models.students import Student as StudentModel   # ✅ 학급(class_id) 참조용
from schemas.attendance import Attendance as AttendanceSchema

router = APIRouter(prefix="/attendance", tags=["attendance"])

# ==========================================================
# [공통] DB 세션 관리
# - 모든 요청에서 DB 연결을 생성하고 종료하는 역할
# - try/finally 구조로 항상 close 보장 → connection leak 방지
# ==========================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================================
# [공통] 상태 매핑 (DB 값 → 응답 값)
# - DB에는 한글 상태값('출석', '결석', '지각', '조회')이 저장됨
# - API 응답에서는 영어 상태값('present', 'absent', 'late', 'checkin')으로 변환
# - 이유:
#   1) 프론트엔드/외부 API 연동 시 인코딩 문제 방지
#   2) 국제화(i18n) 확장 시 언어 매핑이 용이
# ==========================================================
STATUS_MAP = {
    "출석": "present",
    "결석": "absent",
    "지각": "late",
    "조회": "checkin"
}
def convert_status(status: str) -> str:
    return STATUS_MAP.get(status, status)

# ==========================================================
# [1단계] CRUD 기본 라우터 - 루트 경로 우선 처리
# ==========================================================

# ✅ [CREATE] 출결 추가
# - 특정 날짜, 특정 학생의 출결 상태를 새로 기록할 때 사용
# - 예: 교사가 오늘 학생의 등교 여부를 입력
# - 결과: 성공 시 생성된 출결 데이터 반환
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
            "status": convert_status(db_attendance.status),  # 상태값은 영어로 변환
            "reason": db_attendance.reason,
            "message": "Attendance record created successfully"
        }
    }

# ✅ [READ] 전체 출결 조회
# - 모든 학생의 출결 기록을 전부 가져옴
# - 관리자/교사가 학급 전체 출석부를 확인할 때 사용
# - 결과: 리스트 형태로 반환, 프론트에서는 테이블로 표시 가능
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
                "status": convert_status(r.status),
                "reason": r.reason
            }
            for r in records
        ]
    }

# ==========================================================
# [2단계] 정적 요약 라우터 - 구체적인 경로들
# ==========================================================

# ✅ [DAILY SUMMARY] 특정 날짜 출석 현황 요약
# - 하루 동안 전체 학생의 출결 현황을 요약해서 제공
# - 교사가 "오늘 반 출석률"을 빠르게 확인할 때 유용
# - 결과: 총원, 출석/결석/지각/조회 인원, 출석률 %
@router.get("/daily-summary")
def get_daily_attendance_summary(
    date: str = Query(..., description="조회할 날짜 (예: 2025-07-26)"),
    db: Session = Depends(get_db),
):
    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    records = db.query(AttendanceModel).filter(AttendanceModel.date == target_date).all()

    total = len(records)
    status_counter = Counter([r.status for r in records])  # 상태별 인원 수 카운트

    present = status_counter.get("출석", 0)
    absent = status_counter.get("결석", 0)
    late = status_counter.get("지각", 0)
    checkin = status_counter.get("조회", 0)
    rate = round((present / total) * 100, 1) if total else 0  # 출석률 계산

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

# ✅ [WEEKLY SUMMARY] 특정 주간 출결 평균 + 결석 사유 분석
# - 지정된 기간 동안의 일별 출석률을 계산하여 주간 평균을 냄
# - 동시에 결석 사유 데이터를 수집 → 가장 많이 발생한 사유 분석
# - 결과: 주간 평균 출석률, 최다 결석 사유, 비율
@router.get("/weekly-summary")
def get_weekly_attendance_summary(
    start_date: str = Query(..., description="시작일 (예: 2025-07-22)"),
    end_date: str = Query(..., description="종료일 (예: 2025-07-26)"),
    db: Session = Depends(get_db),
):
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    records = db.query(AttendanceModel).filter(AttendanceModel.date.between(start, end)).all()

    # 날짜별 출석률 계산
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

    # 결석 사유 분석
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
            "total_absent": len(reasons)
        }
    }

# ✅ [MONTHLY SUMMARY] 특정 반(class_id)의 월간 출결 통계
# - 학급 단위로 월별 출결 데이터를 집계
# - 학급 보고서, 학부모 안내 자료에 활용
# - 결과: 반별 출석/결석/지각 수치 및 출석률 %
@router.get("/monthly-summary")
def get_monthly_attendance_summary(
    class_id: int,
    month: str = Query(..., description="YYYY-MM 형식 (예: 2025-07)"),
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
# [3단계] 혼합 라우터 - 일부 정적, 일부 동적
# ==========================================================

# ✅ [STUDENT SUMMARY] 특정 학생 누적 출결 현황
# - 한 학생의 전체 출결 이력을 집계
# - 학부모 상담, 생활기록부 작성 시 자주 활용
# - 결과: 총 출결 수, 출석/결석/지각 횟수, 출석률 %
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

# ✅ [CLASS SUMMARY] 특정 반 전체 출결 통계
# - 한 반에 속한 모든 학생의 출결을 집계
# - 학급 단위 출석 현황, 학부모 안내 자료에 활용
# - 결과: 반별 총 출석/결석/지각 횟수와 출석률 %
@router.get("/class/{class_id}/summary")
def get_class_attendance_summary(class_id: int, db: Session = Depends(get_db)):
    records = (
        db.query(AttendanceModel)
        .join(StudentModel, AttendanceModel.student_id == StudentModel.id)
        .filter(StudentModel.class_id == class_id)
        .all()
    )
    if not records:
        return {"success": False, "error": {"code": 404, "message": "Attendance records not found for class"}}

    total = len(records)
    present = sum(1 for r in records if r.status == "출석")
    absent = sum(1 for r in records if r.status == "결석")
    late = sum(1 for r in records if r.status == "지각")
    rate = round((present / total) * 100, 1) if total else 0

    return {
        "success": True,
        "data": {
            "class_id": class_id,
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "attendance_rate": f"{rate}%"
        }
    }

# ==========================================================
# [4단계] 완전 동적 라우터 - 맨 마지막에 배치
# ==========================================================

# ✅ [READ] 출결 상세 조회
# - 출결 ID로 단일 기록을 조회
# - 이유: 특정 기록(예: 7월 1일, A학생 결석 사유)을 확인할 때 필요
@router.get("/{attendance_id}")
def read_attendance(attendance_id: int, db: Session = Depends(get_db)):
    attendance = db.query(AttendanceModel).filter(AttendanceModel.id == attendance_id).first()
    if attendance is None:
        return {"success": False, "error": {"code": 404, "message": "Attendance record not found"}}
    return {
        "success": True,
        "data": {
            "id": attendance.id,
            "student_id": attendance.student_id,
            "date": str(attendance.date),
            "status": convert_status(attendance.status),
            "reason": attendance.reason
        }
    }

# ✅ [UPDATE] 출결 수정
# - 기존에 입력된 출결 상태를 변경
# - 예: 잘못 입력된 '결석'을 '출석'으로 수정
@router.put("/{attendance_id}")
def update_attendance(attendance_id: int, updated: AttendanceSchema, db: Session = Depends(get_db)):
    attendance = db.query(AttendanceModel).filter(AttendanceModel.id == attendance_id).first()
    if attendance is None:
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
            "status": convert_status(attendance.status),
            "reason": attendance.reason,
            "message": "Attendance record updated successfully"
        }
    }

# ✅ [DELETE] 출결 삭제
# - 특정 출결 기록을 완전히 제거
# - 예: 중복 입력, 잘못 입력된 출결 삭제
@router.delete("/{attendance_id}")
def delete_attendance(attendance_id: int, db: Session = Depends(get_db)):
    attendance = db.query(AttendanceModel).filter(AttendanceModel.id == attendance_id).first()
    if attendance is None:
        return {"success": False, "error": {"code": 404, "message": "Attendance record not found"}}

    db.delete(attendance)
    db.commit()
    return {
        "success": True,
        "data": {
            "attendance_id": attendance_id,
            "message": "Attendance record deleted successfully"
        }
    }
