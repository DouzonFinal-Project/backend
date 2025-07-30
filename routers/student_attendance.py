from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.student_attendance import StudentAttendance as AttendanceModel
from schemas.student_info import StudentInfo as AttendanceSchema
from datetime import date

router = APIRouter(prefix="/attendance", tags=["출석 API"])

# ✅ DB 세션 의존성 주입 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 출석 정보 등록
@router.post("/", response_model=AttendanceSchema)
def create_attendance(attendance: AttendanceSchema, db: Session = Depends(get_db)):
    db_attendance = AttendanceModel(**attendance.dict())
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

# ✅ [READ] 전체 출석 정보 조회
@router.get("/", response_model=list[AttendanceSchema])
def read_all_attendance(db: Session = Depends(get_db)):
    return db.query(AttendanceModel).all()

# ✅ [READ] 특정 날짜로 필터링
@router.get("/date/{query_date}", response_model=list[AttendanceSchema])
def read_attendance_by_date(query_date: date, db: Session = Depends(get_db)):
    result = db.query(AttendanceModel).filter(AttendanceModel.date == query_date).all()
    return result

# ✅ [READ] 특정 학생 출석 조회
@router.get("/student/{student_id}", response_model=list[AttendanceSchema])
def read_attendance_by_student(student_id: int, db: Session = Depends(get_db)):
    result = db.query(AttendanceModel).filter(AttendanceModel.student_id == student_id).all()
    return result

# ✅ [UPDATE] 출석 정보 수정 (student_id + date 기준)
@router.put("/{student_id}/{query_date}", response_model=AttendanceSchema)
def update_attendance(student_id: int, query_date: date, updated: AttendanceSchema, db: Session = Depends(get_db)):
    attendance = db.query(AttendanceModel).filter(
        AttendanceModel.student_id == student_id,
        AttendanceModel.date == query_date
    ).first()

    if not attendance:
        raise HTTPException(status_code=404, detail="출석 정보가 없습니다.")

    for field, value in updated.dict().items():
        setattr(attendance, field, value)

    db.commit()
    db.refresh(attendance)
    return attendance

# ✅ [DELETE] 출석 정보 삭제 (student_id + date 기준)
@router.delete("/{student_id}/{query_date}")
def delete_attendance(student_id: int, query_date: date, db: Session = Depends(get_db)):
    attendance = db.query(AttendanceModel).filter(
        AttendanceModel.student_id == student_id,
        AttendanceModel.date == query_date
    ).first()

    if not attendance:
        raise HTTPException(status_code=404, detail="출석 정보가 없습니다.")

    db.delete(attendance)
    db.commit()
    return {"message": "출석 정보가 삭제되었습니다."}
