from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.attendance import Attendance as AttendanceModel
from schemas.attendance import Attendance as AttendanceSchema
from datetime import datetime
from collections import Counter
from sqlalchemy import func  # ✅ 월별 통계 계산용

router = APIRouter(prefix="/attendance", tags=["출결"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ [요약] 특정 날짜 기준 출석 현황 요약
@router.get("/daily-summary")
def get_daily_attendance_summary(
    date: str = Query(..., description="조회할 날짜 (예: 2025-07-26)"),
    db: Session = Depends(get_db),
):
    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    records = db.query(AttendanceModel).filter(AttendanceModel.date == target_date).all()

    total = len(records)
    status_counter = Counter([r.status for r in records])

    출석 = status_counter.get("출석", 0)
    결석 = status_counter.get("결석", 0)
    지각 = status_counter.get("지각", 0)
    조회 = status_counter.get("조회", 0)

    출석률 = round((출석 / total) * 100, 1) if total else 0

    return {
        "날짜": date,
        "총원": total,
        "출석": 출석,
        "결석": 결석,
        "지각": 지각,
        "조회": 조회,
        "출석률": f"{출석률}%",
    }


# ✅ [요약] 특정 주간 기준 출결 평균 및 결석 사유 분석
@router.get("/weekly-summary")
def get_weekly_attendance_summary(
    start_date: str = Query(..., description="시작일 (예: 2025-07-22)"),
    end_date: str = Query(..., description="종료일 (예: 2025-07-26)"),
    db: Session = Depends(get_db),
):
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    records = db.query(AttendanceModel).filter(AttendanceModel.date.between(start, end)).all()

    # 날짜별 출석률 평균
    grouped = {}
    for r in records:
        grouped.setdefault(r.date, []).append(r)

    total_days = len(grouped)
    total_출석률 = 0

    for day_records in grouped.values():
        day_total = len(day_records)
        day_출석 = sum(1 for r in day_records if r.status == "출석")
        total_출석률 += (day_출석 / day_total * 100) if day_total else 0

    avg_출석률 = round(total_출석률 / total_days, 1) if total_days else 0

    # 결석 사유 분석
    reasons = [r.reason for r in records if r.status == "결석" and r.reason]
    reason_counter = Counter(reasons)
    top_reason = reason_counter.most_common(1)[0] if reason_counter else ("없음", 0)

    return {
        "기간": f"{start_date} ~ {end_date}",
        "총 출결 수": len(records),
        "평균 출석률": f"{avg_출석률}%",
        "최다 결석 사유": top_reason[0],
        "비율": f"{round((top_reason[1] / len(reasons)) * 100, 1)}%" if reasons else "0%",
        "총 결석 건수": len(reasons),
    }


# ✅ [월간 요약] 특정 반(class_id)의 월별 출결 통계
@router.get("/monthly-summary")
def get_monthly_attendance_summary(
    class_id: int,
    month: str = Query(..., description="YYYY-MM 형식 (예: 2025-07)"),
    db: Session = Depends(get_db)
):
    year, mon = map(int, month.split("-"))
    records = (
        db.query(AttendanceModel)
        .filter(AttendanceModel.class_id == class_id)
        .filter(func.year(AttendanceModel.date) == year)
        .filter(func.month(AttendanceModel.date) == mon)
        .all()
    )

    total = len(records)
    출석 = sum(1 for r in records if r.status == "출석")
    결석 = sum(1 for r in records if r.status == "결석")
    지각 = sum(1 for r in records if r.status == "지각")

    출석률 = round((출석 / total) * 100, 1) if total else 0

    return {
        "class_id": class_id,
        "월": month,
        "총 기록": total,
        "출석": 출석,
        "결석": 결석,
        "지각": 지각,
        "출석률": f"{출석률}%"
    }


# ✅ [학생 요약] 특정 학생의 누적 출결 현황
@router.get("/student/{student_id}/summary")
def get_student_attendance_summary(student_id: int, db: Session = Depends(get_db)):
    records = db.query(AttendanceModel).filter(AttendanceModel.student_id == student_id).all()
    if not records:
        raise HTTPException(status_code=404, detail="해당 학생의 출결 정보가 없습니다.")

    total = len(records)
    출석 = sum(1 for r in records if r.status == "출석")
    결석 = sum(1 for r in records if r.status == "결석")
    지각 = sum(1 for r in records if r.status == "지각")

    출석률 = round((출석 / total) * 100, 1) if total else 0

    return {
        "student_id": student_id,
        "총 기록": total,
        "출석": 출석,
        "결석": 결석,
        "지각": 지각,
        "출석률": f"{출석률}%"
    }


# ✅ [반 요약] 특정 반 전체 출결 통계
@router.get("/class/{class_id}/summary")
def get_class_attendance_summary(class_id: int, db: Session = Depends(get_db)):
    records = db.query(AttendanceModel).filter(AttendanceModel.class_id == class_id).all()
    if not records:
        raise HTTPException(status_code=404, detail="해당 반의 출결 정보가 없습니다.")

    total = len(records)
    출석 = sum(1 for r in records if r.status == "출석")
    결석 = sum(1 for r in records if r.status == "결석")
    지각 = sum(1 for r in records if r.status == "지각")

    출석률 = round((출석 / total) * 100, 1) if total else 0

    return {
        "class_id": class_id,
        "총 기록": total,
        "출석": 출석,
        "결석": 결석,
        "지각": 지각,
        "출석률": f"{출석률}%"
    }


# ✅ [CREATE] 출결 추가
@router.post("/", response_model=AttendanceSchema)
def create_attendance(attendance: AttendanceSchema, db: Session = Depends(get_db)):
    db_attendance = AttendanceModel(**attendance.model_dump())
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance


# ✅ [READ] 전체 출결 조회
@router.get("/", response_model=list[AttendanceSchema])
def read_attendance_list(db: Session = Depends(get_db)):
    return db.query(AttendanceModel).all()


# ✅ [READ] 출결 상세 조회
@router.get("/{attendance_id}", response_model=AttendanceSchema)
def read_attendance(attendance_id: int, db: Session = Depends(get_db)):
    attendance = db.query(AttendanceModel).filter(AttendanceModel.id == attendance_id).first()
    if attendance is None:
        raise HTTPException(status_code=404, detail="출결 정보를 찾을 수 없습니다")
    return attendance


# ✅ [UPDATE] 출결 수정
@router.put("/{attendance_id}", response_model=AttendanceSchema)
def update_attendance(attendance_id: int, updated: AttendanceSchema, db: Session = Depends(get_db)):
    attendance = db.query(AttendanceModel).filter(AttendanceModel.id == attendance_id).first()
    if attendance is None:
        raise HTTPException(status_code=404, detail="출결 정보를 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(attendance, key, value)
    db.commit()
    db.refresh(attendance)
    return attendance


# ✅ [DELETE] 출결 삭제
@router.delete("/{attendance_id}")
def delete_attendance(attendance_id: int, db: Session = Depends(get_db)):
    attendance = db.query(AttendanceModel).filter(AttendanceModel.id == attendance_id).first()
    if attendance is None:
        raise HTTPException(status_code=404, detail="출결 정보를 찾을 수 없습니다")
    db.delete(attendance)
    db.commit()
    return {"message": "출결 정보가 성공적으로 삭제되었습니다"}
