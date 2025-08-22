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


# ==========================================================
# [1단계] CRUD 기본 라우터 - 루트 경로 우선 처리
# ==========================================================

# ✅ [CREATE] 생활기록 추가 - POST 메서드이므로 순서 무관
@router.post("/", response_model=SchoolReportSchema)
def create_school_report(report: SchoolReportSchema, db: Session = Depends(get_db)):
    db_report = SchoolReportModel(**report.model_dump())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


# ✅ [READ] 전체 생활기록 조회 - 반드시 동적 라우터보다 먼저!
@router.get("/", response_model=list[SchoolReportSchema])
def read_school_reports(db: Session = Depends(get_db)):
    return db.query(SchoolReportModel).all()


# ==========================================================
# [2단계] 혼합 라우터 - 일부 정적, 일부 동적 (중간 우선순위)
# ==========================================================

# ✅ [READ] 특정 학생 생활기록부
@router.get("/student/{student_id}")
def get_student_school_report(student_id: int, db: Session = Depends(get_db)):
    reports = db.query(SchoolReportModel).filter(SchoolReportModel.student_id == student_id).all()
    if not reports:
        raise HTTPException(status_code=404, detail="해당 학생의 생활기록부가 없습니다")
    return reports


# ✅ [READ] 특정 반(class_id)의 생활기록부 목록
@router.get("/class/{class_id}")
def get_class_school_reports(class_id: int, db: Session = Depends(get_db)):
    reports = db.query(SchoolReportModel).filter(SchoolReportModel.class_id == class_id).all()
    if not reports:
        raise HTTPException(status_code=404, detail="해당 반의 생활기록부가 없습니다")
    return reports


# ==========================================================
# [3단계] Export/Action 라우터 - 동적이지만 구체적 경로
# ==========================================================

# ✅ [EXPORT] 생활기록부 PDF 출력 (프론트엔드에서 처리 예정)
@router.get("/{report_id}/export/pdf")
def export_school_report_pdf(report_id: int):
    return {"message": f"Report {report_id} PDF export 성공"}


# ✅ [SEND] 생활기록부 이메일 발송 (향후 구현 예정)
@router.post("/{report_id}/send-email")
def send_school_report_email(report_id: int, email: str):
    # TODO: 실제 이메일 발송 로직 구현 필요
    # - SMTP 서버 설정 (Gmail, AWS SES 등)
    # - 이메일 템플릿 작성
    # - 첨부파일 처리 (PDF 생성 후 첨부)
    return {"message": f"Report {report_id} 이메일 {email}로 발송 완료"}


# ==========================================================
# [4단계] 완전 동적 라우터 - 맨 마지막에 배치!
# ==========================================================

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