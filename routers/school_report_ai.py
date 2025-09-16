# routers/school_report_ai.py
import os
import json
from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.school_report import SchoolReport as SchoolReportModel
from models.students import Student as StudentModel
from schemas.school_report import SchoolReport as SchoolReportSchema
from typing import List, Optional
from pydantic import BaseModel, Field
import logging
import asyncio

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/school_report_ai", tags=["생활기록부AI"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 요청 바디 스키마 (개선된 옵션들)
class GenerateCommentRequest(BaseModel):
    tone: str = Field(default="정중하고 공식적", description="어조 설정")
    length: str = Field(default="상세히", description="길이 설정") 
    focus_areas: List[str] = Field(default=["행동특성", "또래관계", "진로희망"], description="집중할 영역")
    include_suggestions: bool = Field(default=True, description="개선 제안 포함 여부")
    academic_context: Optional[str] = Field(default=None, description="학업 맥락")
    
    class Config:
        schema_extra = {
            "example": {
                "tone": "정중하고 공식적",
                "length": "상세히",
                "focus_areas": ["행동특성", "또래관계", "진로희망"],
                "include_suggestions": True,
                "academic_context": "수학과 과학 분야에 관심이 많음"
            }
        }

# 응답 스키마
class GenerateCommentResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[dict] = None
    message: str

def get_gemini_client():
    """Gemini 클라이언트 초기화"""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("Google API Key가 설정되지 않음")
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
        logger.info(f"Gemini 클라이언트 초기화 성공: {model_name}")
        return client
    except Exception as e:
        logger.error(f"Gemini 클라이언트 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"AI 모델 초기화 실패: {str(e)}")

def create_comment_prompt(report_data: dict, request: GenerateCommentRequest) -> str:
    """생활기록부 코멘트 생성을 위한 프롬프트 생성"""
    
    # 길이별 토큰 가이드라인
    length_guide = {
        "짧게": "5-7문장으로 핵심만 간결하게",
        "표준": "9-12문장으로 적절한 분량의",
        "상세히": "14-17문장으로 구체적이고 상세한"
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
        if report_data["behavior_summary"].strip():
            focus_content.append(f"행동특성: {report_data['behavior_summary']}")
    
    if "또래관계" in request.focus_areas and report_data.get("peer_relation"):
        if report_data["peer_relation"].strip():
            focus_content.append(f"또래관계: {report_data['peer_relation']}")
    
    if "진로희망" in request.focus_areas and report_data.get("career_aspiration"):
        if report_data["career_aspiration"].strip():
            focus_content.append(f"진로희망: {report_data['career_aspiration']}")
    
    # 담임교사 피드백 항상 포함 (있는 경우)
    if report_data.get("teacher_feedback") and report_data["teacher_feedback"].strip():
        focus_content.append(f"담임교사 의견: {report_data['teacher_feedback']}")
    
    # 학업 맥락 추가
    academic_info = ""
    if request.academic_context and request.academic_context.strip():
        academic_info = f"\n학업 맥락: {request.academic_context}"
    
    # 개선 제안 가이드라인
    suggestion_guide = ""
    if request.include_suggestions:
        suggestion_guide = "\n- 학생의 강점을 바탕으로 한 구체적인 발전 방향을 제시해주세요."
    
    # 내용이 부족한 경우 체크
    if not focus_content:
        raise ValueError("생성할 수 있는 내용이 부족합니다. 행동특성, 또래관계, 진로희망, 교사피드백 중 최소 하나는 입력되어야 합니다.")
    
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
- 개인정보나 민감한 내용은 포함하지 마세요.

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
            logger.warning(f"생활기록부를 찾을 수 없음: report_id={report_id}")
            return GenerateCommentResponse(
                success=False,
                error={"code": 404, "message": "해당 생활기록을 찾을 수 없습니다"},
                message="생활기록부를 찾을 수 없습니다"
            )

        # 2. 학생 정보도 함께 조회
        student = db.query(StudentModel).filter(StudentModel.id == report.student_id).first()
        
        # 3. 생활기록 데이터 준비
        report_data = {
            "behavior_summary": report.behavior_summary or "",
            "peer_relation": report.peer_relation or "",
            "career_aspiration": report.career_aspiration or "",
            "teacher_feedback": report.teacher_feedback or "",
            "year": report.year,
            "semester": report.semester
        }
        
        # 학생 정보 추가 (있는 경우)
        if student:
            report_data.update({
                "student_name": student.student_name,
                "class_id": getattr(student, 'class_id', None)
            })
            logger.info(f"학생 정보 포함: {student.student_name}")

        # 4. 데이터 유효성 검사
        content_fields = [
            report_data.get("behavior_summary", "").strip(), 
            report_data.get("peer_relation", "").strip(), 
            report_data.get("career_aspiration", "").strip(), 
            report_data.get("teacher_feedback", "").strip()
        ]
        
        if not any(field for field in content_fields):
            logger.warning(f"생성 가능한 데이터 부족: report_id={report_id}")
            return GenerateCommentResponse(
                success=False,
                error={
                    "code": 400, 
                    "message": "생성할 수 있는 내용이 부족합니다. 행동특성, 또래관계, 진로희망, 교사피드백 중 최소 하나는 입력되어야 합니다."
                },
                message="생성 가능한 데이터가 부족합니다"
            )

        # 5. Gemini 클라이언트 초기화
        logger.info("Gemini 클라이언트 초기화")
        gemini_client = get_gemini_client()
        
        # 6. 프롬프트 생성
        try:
            prompt = create_comment_prompt(report_data, request)
            logger.info(f"프롬프트 생성 완료: {len(prompt)} 문자")
        except ValueError as ve:
            logger.error(f"프롬프트 생성 실패: {ve}")
            return GenerateCommentResponse(
                success=False,
                error={"code": 400, "message": str(ve)},
                message="프롬프트 생성에 실패했습니다"
            )
        
        # 7. AI 모델 호출
        logger.info("Gemini 모델 호출 시작")
        try:
            messages = [HumanMessage(content=prompt)]
            
            # asyncio를 사용하여 타임아웃 설정
            response = await asyncio.wait_for(
                gemini_client.ainvoke(messages),
                timeout=30.0  # 30초 타임아웃
            )
        except asyncio.TimeoutError:
            logger.error("Gemini API 호출 타임아웃")
            return GenerateCommentResponse(
                success=False,
                error={"code": 408, "message": "AI 모델 응답 시간 초과"},
                message="AI 모델 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요."
            )
        except Exception as e:
            logger.error(f"Gemini API 호출 실패: {e}")
            return GenerateCommentResponse(
                success=False,
                error={"code": 503, "message": f"AI 서비스 호출 실패: {str(e)}"},
                message="AI 서비스에 일시적인 문제가 발생했습니다"
            )
        
        # 8. 응답 처리
        generated_comment = response.content.strip() if response and response.content else ""
        
        if not generated_comment:
            logger.error("AI 모델에서 빈 응답 수신")
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
                "metadata": {
                    "character_count": len(generated_comment),
                    "word_count": len(generated_comment.split()),
                    "sentence_count": len([s for s in generated_comment.split('.') if s.strip()]),
                    "year": report.year,
                    "semester": report.semester
                }
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
            error={"code": 500, "message": f"시스템 오류가 발생했습니다: {str(e)}"},
            message="시스템 오류가 발생했습니다"
        )

@router.get("/{report_id}/generate-preview")
async def preview_generation_options(report_id: int, db: Session = Depends(get_db)):
    """코멘트 생성 전 미리보기 및 옵션 확인"""
    try:
        report = db.query(SchoolReportModel).filter(SchoolReportModel.id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="생활기록을 찾을 수 없습니다")
        
        # 학생 정보 조회
        student = db.query(StudentModel).filter(StudentModel.id == report.student_id).first()
        
        # 사용 가능한 콘텐츠 분석
        available_content = {}
        content_quality_score = 0
        
        if report.behavior_summary and report.behavior_summary.strip():
            char_count = len(report.behavior_summary.strip())
            available_content["행동특성"] = {
                "length": char_count,
                "preview": report.behavior_summary[:50] + "..." if char_count > 50 else report.behavior_summary,
                "quality": "충분" if char_count > 30 else "부족"
            }
            content_quality_score += 1
            
        if report.peer_relation and report.peer_relation.strip():
            char_count = len(report.peer_relation.strip())
            available_content["또래관계"] = {
                "length": char_count,
                "preview": report.peer_relation[:50] + "..." if char_count > 50 else report.peer_relation,
                "quality": "충분" if char_count > 20 else "부족"
            }
            content_quality_score += 1
            
        if report.career_aspiration and report.career_aspiration.strip():
            char_count = len(report.career_aspiration.strip())
            available_content["진로희망"] = {
                "length": char_count,
                "preview": report.career_aspiration[:50] + "..." if char_count > 50 else report.career_aspiration,
                "quality": "충분" if char_count > 20 else "부족"
            }
            content_quality_score += 1
            
        if report.teacher_feedback and report.teacher_feedback.strip():
            char_count = len(report.teacher_feedback.strip())
            available_content["담임피드백"] = {
                "length": char_count,
                "preview": report.teacher_feedback[:50] + "..." if char_count > 50 else report.teacher_feedback,
                "quality": "충분" if char_count > 30 else "부족"
            }
            content_quality_score += 1
        
        # 추천 설정
        recommended_settings = {
            "tone": "정중하고 공식적",
            "length": "상세히" if content_quality_score >= 3 else "표준",
            "focus_areas": list(available_content.keys())
        }
        
        # 생성 가능성 평가
        generation_assessment = {
            "ready": content_quality_score > 0,
            "quality": "우수" if content_quality_score >= 3 else "양호" if content_quality_score >= 2 else "부족",
            "recommendations": []
        }
        
        if content_quality_score == 0:
            generation_assessment["recommendations"].append("최소 한 개 영역의 내용을 입력해주세요")
        elif content_quality_score == 1:
            generation_assessment["recommendations"].append("더 풍부한 코멘트를 위해 추가 영역 내용 입력을 권장합니다")
        elif content_quality_score >= 3:
            generation_assessment["recommendations"].append("충분한 내용으로 상세한 코멘트 생성이 가능합니다")
        
        return {
            "success": True,
            "data": {
                "report_info": {
                    "id": report_id,
                    "year": report.year,
                    "semester": report.semester,
                    "student_name": student.student_name if student else None,
                    "student_id": report.student_id
                },
                "available_content": available_content,
                "recommended_settings": recommended_settings,
                "generation_assessment": generation_assessment,
                "available_options": {
                    "tones": ["정중하고 공식적", "친근한", "간결한"],
                    "lengths": ["짧게", "표준", "상세히"],
                    "focus_areas": ["행동특성", "또래관계", "진로희망"]
                }
            },
            "message": "생성 옵션 미리보기 완료"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"미리보기 생성 중 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="미리보기 생성 중 오류가 발생했습니다")