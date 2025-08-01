from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.school_report import SchoolReport as SchoolReportModel
from schemas.school_report import SchoolReport as SchoolReportSchema

router = APIRouter(prefix="/school_report", tags=["생활기록부"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [CREATE] 생활기록 추가
@router.post("/", response_model=SchoolReportSchema)
def create_school_report(report: SchoolReportSchema, db: Session = Depends(get_db)):
    db_report = SchoolReportModel(**report.model_dump())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

# ✅ [READ] 전체 생활기록 조회
@router.get("/", response_model=list[SchoolReportSchema])
def read_school_reports(db: Session = Depends(get_db)):
    return db.query(SchoolReportModel).all()

# ✅ [READ] 생활기록 상세 조회
@router.get("/{report_id}", response_model=SchoolReportSchema)
def read_school_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(SchoolReportModel).filter(SchoolReportModel.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="생활기록을 찾을 수 없습니다")
    return report

# ✅ [UPDATE] 생활기록 수정
@router.put("/{report_id}", response_model=SchoolReportSchema)
def update_school_report(report_id: int, updated: SchoolReportSchema, db: Session = Depends(get_db)):
    report = db.query(SchoolReportModel).filter(SchoolReportModel.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="생활기록을 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(report, key, value)
    db.commit()
    db.refresh(report)
    return report

# ✅ [DELETE] 생활기록 삭제
@router.delete("/{report_id}")
def delete_school_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(SchoolReportModel).filter(SchoolReportModel.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="생활기록을 찾을 수 없습니다")
    db.delete(report)
    db.commit()
    return {"message": "생활기록이 성공적으로 삭제되었습니다"}
