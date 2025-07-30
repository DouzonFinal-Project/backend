from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.school_report import SchoolReport as SchoolReportModel
from schemas.school_report import SchoolReport, SchoolReportCreate

router = APIRouter(prefix="/school-report", tags=["학교생활 종합보고서"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 보고서 등록
@router.post("/", response_model=SchoolReport)
def create_report(report: SchoolReportCreate, db: Session = Depends(get_db)):
    db_report = SchoolReportModel(**report.dict())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

# ✅ [READ] 전체 보고서 조회
@router.get("/", response_model=list[SchoolReport])
def read_reports(db: Session = Depends(get_db)):
    return db.query(SchoolReportModel).all()

# ✅ [READ] 특정 학생의 보고서 조회
@router.get("/{student_id}", response_model=list[SchoolReport])
def read_student_reports(student_id: int, db: Session = Depends(get_db)):
    result = db.query(SchoolReportModel).filter(SchoolReportModel.student_id == student_id).all()
    if not result:
        raise HTTPException(status_code=404, detail="해당 학생의 보고서를 찾을 수 없습니다.")
    return result

# ✅ [UPDATE]
@router.put("/{report_id}", response_model=SchoolReport)
def update_report(report_id: int, updated: SchoolReportCreate, db: Session = Depends(get_db)):
    report = db.query(SchoolReportModel).filter(SchoolReportModel.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
    for key, value in updated.dict().items():
        setattr(report, key, value)
    db.commit()
    db.refresh(report)
    return report

# ✅ [DELETE]
@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(SchoolReportModel).filter(SchoolReportModel.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
    db.delete(report)
    db.commit()
    return {"message": "보고서가 삭제되었습니다."}
