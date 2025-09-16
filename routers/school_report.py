import os
import json
from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.school_report import SchoolReport as SchoolReportModel
from models.students import Student as StudentModel
from schemas.school_report import SchoolReport as SchoolReportSchema
from typing import List, Optional
from pydantic import BaseModel
import logging

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/school_report", tags=["생활기록부"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 요청 바디 스키마 (개선된 옵션들)
class GenerateCommentRequest(BaseModel):
    tone: str = "정중하고 공식적"        # 예: "정중하고 공식적", "친근한", "간결한"
    length: str = "상세히"               # 예: "짧게", "표준", "상세히"
    focus_areas: List[str] = ["행동특성", "또래관계", "진로희망"]  # 집중할 영역
    include_suggestions: bool = True     # 개선 제안 포함 여부
    academic_context: Optional[str] = None  # 학업 맥락 (선택사항)

# 응답 스키마
class GenerateCommentResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[dict] = None
    message: str

# ==========================================================
# 기존 CRUD 라우터들은 그대로 유지...
# ==========================================================

# CREATE
@router.post("/")
def create_school_report(report: SchoolReportSchema, db: Session = Depends(get_db)):
    db_report = SchoolReportModel(**report.model_dump())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return {
        "success": True,
        "data": {
            "id": db_report.id,
            "student_id": db_report.student_id,
            "year": db_report.year,
            "semester": db_report.semester,
            "behavior_summary": db_report.behavior_summary,
            "peer_relation": db_report.peer_relation,
            "career_aspiration": db_report.career_aspiration,
            "teacher_feedback": db_report.teacher_feedback
        },
        "message": "생활기록이 성공적으로 추가되었습니다"
    }

# READ - 전체 조회
@router.get("/")
def read_school_reports(db: Session = Depends(get_db)):
    records = db.query(SchoolReportModel).all()
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "student_id": r.student_id,
                "year": r.year,
                "semester": r.semester,
                "behavior_summary": r.behavior_summary,
                "peer_relation": r.peer_relation,
                "career_aspiration": r.career_aspiration,
                "teacher_feedback": r.teacher_feedback
            }
            for r in records
        ],
        "message": "전체 생활기록 조회 완료"
    }

# READ - 특정 학생
@router.get("/student/{student_id}")
def get_student_school_report(student_id: int, db: Session = Depends(get_db)):
    reports = db.query(SchoolReportModel).filter(SchoolReportModel.student_id == student_id).all()
    if not reports:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 학생의 생활기록부가 없습니다"}
        }
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "student_id": r.student_id,
                "year": r.year,
                "semester": r.semester,
                "behavior_summary": r.behavior_summary,
                "peer_relation": r.peer_relation,
                "career_aspiration": r.career_aspiration,
                "teacher_feedback": r.teacher_feedback
            }
            for r in reports
        ],
        "message": f"학생 ID {student_id} 생활기록 조회 성공"
    }

# READ - 특정 반
@router.get("/class/{class_id}")
def get_class_school_reports(class_id: int, db: Session = Depends(get_db)):
    reports = (
        db.query(SchoolReportModel)
        .join(StudentModel, StudentModel.id == SchoolReportModel.student_id)
        .filter(StudentModel.class_id == class_id)
        .all()
    )
    if not reports:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 반의 생활기록부가 없습니다"}
        }
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "student_id": r.student_id,
                "year": r.year,
                "semester": r.semester,
                "behavior_summary": r.behavior_summary,
                "peer_relation": r.peer_relation,
                "career_aspiration": r.career_aspiration,
                "teacher_feedback": r.teacher_feedback
            }
            for r in reports
        ],
        "message": f"반 ID {class_id} 생활기록 조회 성공"
    }

# EXPORT/ACTION 라우터들
@router.get("/{report_id}/export/pdf")
def export_school_report_pdf(report_id: int):
    return {
        "success": True,
        "data": {"report_id": report_id},
        "message": f"생활기록 {report_id} PDF 출력 완료"
    }

@router.post("/{report_id}/send-email")
def send_school_report_email(report_id: int, email: str):
    return {
        "success": True,
        "data": {"report_id": report_id, "recipient": email},
        "message": f"생활기록 {report_id}가 {email}로 발송되었습니다"
    }

# READ - 상세 조회
@router.get("/{report_id}")
def read_school_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(SchoolReportModel).filter(SchoolReportModel.id == report_id).first()
    if report is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "생활기록을 찾을 수 없습니다"}
        }
    return {
        "success": True,
        "data": {
            "id": report.id,
            "student_id": report.student_id,
            "year": report.year,
            "semester": report.semester,
            "behavior_summary": report.behavior_summary,
            "peer_relation": report.peer_relation,
            "career_aspiration": report.career_aspiration,
            "teacher_feedback": report.teacher_feedback
        },
        "message": "생활기록 상세 조회 성공"
    }

# UPDATE
@router.put("/{report_id}")
def update_school_report(report_id: int, updated: SchoolReportSchema, db: Session = Depends(get_db)):
    report = db.query(SchoolReportModel).filter(SchoolReportModel.id == report_id).first()
    if report is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "생활기록을 찾을 수 없습니다"}
        }

    for key, value in updated.model_dump().items():
        setattr(report, key, value)

    db.commit()
    db.refresh(report)
    return {
        "success": True,
        "data": {
            "id": report.id,
            "student_id": report.student_id,
            "year": report.year,
            "semester": report.semester,
            "behavior_summary": report.behavior_summary,
            "peer_relation": report.peer_relation,
            "career_aspiration": report.career_aspiration,
            "teacher_feedback": report.teacher_feedback
        },
        "message": "생활기록이 성공적으로 수정되었습니다"
    }

# DELETE
@router.delete("/{report_id}")
def delete_school_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(SchoolReportModel).filter(SchoolReportModel.id == report_id).first()
    if report is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "생활기록을 찾을 수 없습니다"}
        }

    db.delete(report)
    db.commit()
    return {
        "success": True,
        "data": {"report_id": report_id},
        "message": "생활기록이 성공적으로 삭제되었습니다"
    }

# ==========================================================
# 개선된 AI 코멘트 생성 라우터
# ==========================================================

def get_gemini_client():
    """Gemini 클라이언트 초기화"""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="환경변수 GOOGLE_API_KEY 또는 GEMINI_API_KEY가 설정되어 있지 않습니다"
        )
    
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash-lite")
    
    try:
        client = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.3,
            max_output_tokens=1024,
            convert_system_message_to_human=True
        )
        return client
    except Exception as e:
        logger.error(f"Gemini 클라이언트 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"AI 모델 초기화 실패: {str(e)}")

def create_comment_prompt(report_data: dict, request: GenerateCommentRequest) -> str:
    """생활기록부 코멘트 생성을 위한 프롬프트 생성"""
    
    # 길이별 토큰 가이드라인
    length_guide = {
        "짧게": "2-3문장으로 핵심만 간결하게",
        "표준": "4-6문장으로 적절한 분량의",
        "상세히": "7-10문장으로 구체적이고 상세한"
    }
    
    # 톤별 가이드라인
    tone_guide = {
        "정중하고 공식적": "존댓말과 격식있는 표현을 사용하여 공식적이고 정중한",
        "친근한": "따뜻하고 친근한 어조로 학생을 격려하는",
        "간결한": "명확하고 간결한 표현으로 핵심을 전달하는"
    }
    
    # 집중 영역별 내용 구성
    focus_content = []
    if "행동특성" in request.focus_areas and report_data.get("behavior_summary"):
        focus_content.append(f"행동특성: {report_data['behavior_summary']}")
    if "또래관계" in request.focus_areas and report_data.get("peer_relation"):
        focus_content.append(f"또래관계: {report_data['peer_relation']}")
    if "진로희망" in request.focus_areas and report_data.get("career_aspiration"):
        focus_content.append(f"진로희망: {report_data['career_aspiration']}")
    
    # 담임교사 피드백 항상 포함
    if report_data.get("teacher_feedback"):
        focus_content.append(f"담임교사 의견: {report_data['teacher_feedback']}")
    
    # 학업 맥락 추가
    academic_info = ""
    if request.academic_context:
        academic_info = f"\n학업 맥락: {request.academic_context}"
    
    # 개선 제안 가이드라인
    suggestion_guide = ""
    if request.include_suggestions:
        suggestion_guide = "\n- 학생의 강점을 바탕으로 한 구체적인 발전 방향을 제시해주세요."
    
    prompt = f"""당신은 한국의 초중고등학교 담임교사로서 생활기록부 종합의견을 작성하는 전문가입니다.

다음 학생 정보를 바탕으로 {tone_guide.get(request.tone, "적절한")} 어조로 {length_guide.get(request.length, "적절한 분량의")} 생활기록부 종합의견을 한국어로 작성해주세요.

학생 정보:
{chr(10).join(focus_content)}
{academic_info}

작성 가이드라인:
- 학생의 긍정적인 면을 부각시키되, 객관적이고 구체적으로 서술해주세요.
- 부족한 부분은 완곡하게 표현하고 개선 방향을 제시해주세요.
- 교육적이고 건설적인 내용으로 구성해주세요.
- 생활기록부에 적합한 공식적인 문체를 사용해주세요.{suggestion_guide}

주의사항:
- 과장된 표현은 피해주세요.
- 구체적인 사례나 행동을 언급할 때는 교육적 의미를 부여해주세요.
- 학생의 성장 가능성과 잠재력을 강조해주세요.

생성된 코멘트만 출력해주세요."""

    return prompt

@router.post("/{report_id}/generate-comment")
async def generate_school_report_comment(
    report_id: int,
    request: GenerateCommentRequest = Body(...),
    db: Session = Depends(get_db),
) -> GenerateCommentResponse:
    """
    생활기록부 AI 코멘트 생성
    
    Args:
        report_id: 생활기록부 ID
        request: 생성 옵션 (톤, 길이, 집중영역 등)
        db: 데이터베이스 세션
        
    Returns:
        GenerateCommentResponse: 생성된 코멘트와 메타데이터
    """
    try:
        # 1. 데이터베이스에서 생활기록 조회
        logger.info(f"생활기록부 조회 시작: report_id={report_id}")
        report = db.query(SchoolReportModel).filter(SchoolReportModel.id == report_id).first()
        
        if not report:
            return GenerateCommentResponse(
                success=False,
                error={"code": 404, "message": "해당 생활기록을 찾을 수 없습니다"},
                message="생활기록부를 찾을 수 없습니다"
            )

        # 2. 학생 정보도 함께 조회 (필요시)
        student = db.query(StudentModel).filter(StudentModel.id == report.student_id).first()
        
        # 3. 생활기록 데이터 준비
        report_data = {
            "behavior_summary": report.behavior_summary,
            "peer_relation": report.peer_relation,
            "career_aspiration": report.career_aspiration,
            "teacher_feedback": report.teacher_feedback,
            "year": report.year,
            "semester": report.semester
        }
        
        # 학생 정보 추가 (있는 경우)
        if student:
            report_data.update({
                "student_name": student.student_name,
                "class_id": student.class_id
            })

        # 4. 데이터 유효성 검사
        content_fields = [report_data.get("behavior_summary"), 
                         report_data.get("peer_relation"), 
                         report_data.get("career_aspiration"), 
                         report_data.get("teacher_feedback")]
        
        if not any(field and field.strip() for field in content_fields):
            return GenerateCommentResponse(
                success=False,
                error={"code": 400, "message": "생성할 수 있는 내용이 부족합니다. 행동특성, 또래관계, 진로희망, 교사피드백 중 최소 하나는 입력되어야 합니다."},
                message="생성 가능한 데이터가 부족합니다"
            )

        # 5. Gemini 클라이언트 초기화
        logger.info("Gemini 클라이언트 초기화")
        gemini_client = get_gemini_client()
        
        # 6. 프롬프트 생성
        prompt = create_comment_prompt(report_data, request)
        logger.info(f"프롬프트 생성 완료: {len(prompt)} 문자")
        
        # 7. AI 모델 호출
        logger.info("Gemini 모델 호출 시작")
        messages = [HumanMessage(content=prompt)]
        response = await gemini_client.ainvoke(messages)
        
        # 8. 응답 처리
        generated_comment = response.content.strip()
        
        if not generated_comment:
            return GenerateCommentResponse(
                success=False,
                error={"code": 500, "message": "AI 모델에서 유효한 응답을 받지 못했습니다"},
                message="코멘트 생성에 실패했습니다"
            )

        logger.info(f"코멘트 생성 성공: {len(generated_comment)} 문자")
        
        # 9. 성공 응답 반환
        return GenerateCommentResponse(
            success=True,
            data={
                "report_id": report_id,
                "student_id": report.student_id,
                "student_name": student.student_name if student else None,
                "generated_comment": generated_comment,
                "generation_options": {
                    "tone": request.tone,
                    "length": request.length,
                    "focus_areas": request.focus_areas,
                    "include_suggestions": request.include_suggestions,
                    "academic_context": request.academic_context
                },
                "character_count": len(generated_comment),
                "word_count": len(generated_comment.split())
            },
            message="생활기록부 코멘트가 성공적으로 생성되었습니다"
        )
        
    except HTTPException:
        # 이미 처리된 HTTP 예외는 그대로 전달
        raise
    except Exception as e:
        logger.error(f"코멘트 생성 중 예상치 못한 오류: {e}", exc_info=True)
        return GenerateCommentResponse(
            success=False,
            error={"code": 500, "message": f"코멘트 생성 중 오류가 발생했습니다: {str(e)}"},
            message="시스템 오류가 발생했습니다"
        )

# ==========================================================
# 추가 유틸리티 라우터
# ==========================================================

@router.get("/{report_id}/generate-preview")
async def preview_generation_options(report_id: int, db: Session = Depends(get_db)):
    """코멘트 생성 전 미리보기 및 옵션 확인"""
    report = db.query(SchoolReportModel).filter(SchoolReportModel.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="생활기록을 찾을 수 없습니다")
    
    # 사용 가능한 콘텐츠 분석
    available_content = {}
    if report.behavior_summary and report.behavior_summary.strip():
        available_content["행동특성"] = len(report.behavior_summary)
    if report.peer_relation and report.peer_relation.strip():
        available_content["또래관계"] = len(report.peer_relation)
    if report.career_aspiration and report.career_aspiration.strip():
        available_content["진로희망"] = len(report.career_aspiration)
    if report.teacher_feedback and report.teacher_feedback.strip():
        available_content["담임피드백"] = len(report.teacher_feedback)
    
    return {
        "success": True,
        "data": {
            "report_id": report_id,
            "available_content": available_content,
            "recommended_focus": list(available_content.keys()),
            "content_quality": "충분" if len(available_content) >= 2 else "부족",
            "generation_ready": len(available_content) > 0
        },
        "message": "생성 옵션 미리보기 완료"
    }