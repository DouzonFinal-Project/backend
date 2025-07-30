from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.reports import Report as ReportModel
from schemas.reports import Report as ReportSchema, ReportCreate
from database.db import SessionLocal

router = APIRouter(prefix="/reports", tags=["상담 보고서"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 보고서 등록
@router.post("/", response_model=ReportSchema)
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    db_report = ReportModel(**report.dict())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

# ✅ [READ] 전체 조회
@router.get("/", response_model=list[ReportSchema])
def read_reports(db: Session = Depends(get_db)):
    return db.query(ReportModel).all()

# ✅ [READ] 특정 보고서
@router.get("/{report_id}", response_model=ReportSchema)
def read_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(ReportModel).filter(ReportModel.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
    return report

# ✅ [UPDATE]
@router.put("/{report_id}", response_model=ReportSchema)
def update_report(report_id: int, updated: ReportCreate, db: Session = Depends(get_db)):
    report = db.query(ReportModel).filter(ReportModel.report_id == report_id).first()
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
    report = db.query(ReportModel).filter(ReportModel.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
    db.delete(report)
    db.commit()
    return {"message": "보고서가 삭제되었습니다."}
