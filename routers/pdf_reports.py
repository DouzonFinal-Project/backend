from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.students import Student as StudentModel
from models.reports import Report as ReportModel
from models.grades import Grade as GradeModel
from services.pdf_service import PDFService
from services.ai_client import ai_client

router = APIRouter(prefix="/pdf", tags=["PDF 생성"])

pdf_service = PDFService()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/counseling-report/{student_id}")
async def generate_counseling_pdf(student_id: int, db: Session = Depends(get_db)):
    """상담 보고서 PDF 생성"""
    try:
        # 학생 정보 조회
        student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")
        
        # 상담 기록 조회
        reports = db.query(ReportModel).filter(ReportModel.student_id == student_id).all()
        
        # 성적 정보 조회
        grades = db.query(GradeModel).filter(GradeModel.student_id == student_id).all()
        
        # AI 분석 요청
        ai_analysis = await ai_client.counseling_chat(
            query=f"{student.student_name} 학생에 대한 종합 상담 분석을 해주세요",
            use_rag=True,
            student_name=student.student_name
        )
        
        # PDF 생성 데이터 준비
        pdf_data = {
            "student": student,
            "reports": reports,
            "grades": grades,
            "ai_analysis": ai_analysis.get("data", {}).get("response", "분석 정보 없음"),
            "generated_date": "2024-08-12"
        }
        
        # PDF 생성
        pdf_content = pdf_service.generate_counseling_pdf(pdf_data)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=상담보고서_{student.student_name}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 생성 실패: {str(e)}")

@router.post("/class-summary/{class_id}")
async def generate_class_pdf(class_id: int, db: Session = Depends(get_db)):
    """학급 요약 PDF 생성"""
    try:
        # 학급 학생들 조회
        students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
        if not students:
            raise HTTPException(status_code=404, detail="해당 학급에 학생이 없습니다")
        
        # PDF 생성 데이터 준비
        pdf_data = {
            "students": students,
            "class_id": class_id,
            "generated_date": "2024-08-12"
        }
        
        # PDF 생성
        pdf_content = pdf_service.generate_class_summary_pdf(pdf_data)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=학급요약_{class_id}반.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 생성 실패: {str(e)}")