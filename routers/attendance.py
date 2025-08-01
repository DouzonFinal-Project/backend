from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.attendance import Attendance as AttendanceModel
from schemas.attendance import Attendance as AttendanceSchema

router = APIRouter(prefix="/attendance", tags=["출결"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
