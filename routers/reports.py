from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.reports import Report as ReportModel
from schemas.reports import Report as ReportSchema

router = APIRouter(prefix="/reports", tags=["상담보고서"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 상담보고서 추가
@router.post("/", response_model=ReportSchema)
def create_report(report: ReportSchema, db: Session = Depends(get_db)):
    db_report = ReportModel(**report.model_dump())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

# ✅ [READ] 전체 상담보고서 조회
@router.get("/", response_model=list[ReportSchema])
def read_reports(db: Session = Depends(get_db)):
    return db.query(ReportModel).all()

# ✅ [READ] 상담보고서 상세 조회
@router.get("/{report_id}", response_model=ReportSchema)
def read_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(ReportModel).filter(ReportModel.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="상담보고서를 찾을 수 없습니다")
    return report

# ✅ [UPDATE] 상담보고서 수정
@router.put("/{report_id}", response_model=ReportSchema)
def update_report(report_id: int, updated: ReportSchema, db: Session = Depends(get_db)):
    report = db.query(ReportModel).filter(ReportModel.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="상담보고서를 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(report, key, value)
    db.commit()
    db.refresh(report)
    return report

# ✅ [DELETE] 상담보고서 삭제
@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(ReportModel).filter(ReportModel.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="상담보고서를 찾을 수 없습니다")
    db.delete(report)
    db.commit()
    return {"message": "상담보고서가 성공적으로 삭제되었습니다"}
