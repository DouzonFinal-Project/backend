from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.reports import Report as ReportModel
from schemas.reports import Report as ReportSchema
from typing import List
import datetime

router = APIRouter(prefix="/reports", tags=["리포트 관리"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================
# [1단계] CRUD 기본 라우터 - 루트 경로 우선 처리
# ==========================================================

# ✅ [CREATE] 리포트 생성 (직접 작성) - POST 메서드이므로 순서 무관
@router.post("/", response_model=ReportSchema)
def create_report(report: ReportSchema, db: Session = Depends(get_db)):
    db_report = ReportModel(**report.model_dump())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


# ✅ [READ] 전체 리포트 조회 - 반드시 동적 라우터보다 먼저!
@router.get("/", response_model=List[ReportSchema])
def read_reports(db: Session = Depends(get_db)):
    return db.query(ReportModel).all()


# ==========================================================
# [2단계] 정적 라우터 - 구체적인 경로들
# ==========================================================

# ✅ [REPORT GENERATION] 주간/월간 리포트 자동 생성
@router.post("/generate", response_model=ReportSchema)
def generate_report(report_type: str, start_date: datetime.date, end_date: datetime.date, db: Session = Depends(get_db)):
    """
    report_type: 'weekly', 'monthly', 'analysis' 등
    """
    fake_summary = f"{report_type} 리포트 자동 생성: {start_date} ~ {end_date}"
    db_report = ReportModel(title=f"{report_type} Report", content=fake_summary, type=report_type)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


# ✅ [REPORT PREVIEW] 리포트 미리보기
@router.get("/preview")
def preview_report(report_type: str, start_date: datetime.date, end_date: datetime.date):
    return {
        "report_type": report_type,
        "period": f"{start_date} ~ {end_date}",
        "summary": f"샘플 미리보기: {report_type} 기간 리포트 데이터 요약"
    }


# ✅ [REPORT SUMMARY] 리포트 요약 통계
@router.get("/summary")
def report_summary(report_type: str, db: Session = Depends(get_db)):
    return {
        "report_type": report_type,
        "total_students": 28,
        "attendance_rate": "96.4%",
        "avg_score": 82.3,
        "counseling_count": 3,
        "issues": 2
    }


# ==========================================================
# [3단계] Export/Action 라우터 - 정적이지만 특수 기능
# ==========================================================

# ✅ [EXPORT PDF] PDF 내보내기 (옵션, 프론트 처리 가능)
@router.get("/export/pdf/{report_id}")
def export_pdf(report_id: int):
    return {"message": f"리포트 {report_id} PDF 생성 완료 (샘플)"}


# ==========================================================
# [4단계] 혼합 라우터 - 일부 정적, 일부 동적
# ==========================================================

# ✅ [REPORT DETAILS] 리포트 상세 통계
@router.get("/details/{report_id}")
def report_details(report_id: int, db: Session = Depends(get_db)):
    report = db.query(ReportModel).filter(ReportModel.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
    return {
        "id": report.id,
        "title": report.title,
        "content": report.content,
        "statistics": {
            "성적분석": "과목별 평균, 최고/최저점",
            "출결현황": "결석/지각/조퇴 건수",
            "상담현황": "학생별 상담 기록 수"
        }
    }


# ✅ [SAVE / SUBMIT] 저장 & 제출
@router.post("/save/{report_id}")
def save_report(report_id: int):
    return {"message": f"리포트 {report_id} 임시저장 완료"}


@router.post("/submit/{report_id}")
def submit_report(report_id: int):
    return {"message": f"리포트 {report_id} 최종 제출 완료"}


# ✅ [SEND EMAIL] 이메일 발송
@router.post("/send-email/{report_id}")
def send_report_email(report_id: int, recipient: str):
    return {"message": f"리포트 {report_id}가 {recipient}에게 이메일로 전송되었습니다"}


# ==========================================================
# [5단계] 완전 동적 라우터 - 맨 마지막에 배치!
# ==========================================================

# ✅ [READ] 리포트 상세 조회
@router.get("/{report_id}", response_model=ReportSchema)
def read_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(ReportModel).filter(ReportModel.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
    return report


# ✅ [UPDATE] 리포트 수정
@router.put("/{report_id}", response_model=ReportSchema)
def update_report(report_id: int, updated: ReportSchema, db: Session = Depends(get_db)):
    report = db.query(ReportModel).filter(ReportModel.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(report, key, value)
    db.commit()
    db.refresh(report)
    return report


# ✅ [DELETE] 리포트 삭제
@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(ReportModel).filter(ReportModel.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
    db.delete(report)
    db.commit()
    return {"message": "리포트가 성공적으로 삭제되었습니다"}