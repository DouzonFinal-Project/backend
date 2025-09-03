from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import json
from services.ai_handlers.problem_generator_handler import handle_problem_generation

router = APIRouter(prefix="/problem-generation", tags=["problem-generation"])

@router.post("/generate")
async def generate_problem_set(settings: Dict[str, Any]):
    """
    문제출제설정에 맞는 문제지를 생성합니다.
    
    Args:
        settings: 문제 출제 설정 정보
            - subject: 과목
            - units: 선택된 단원들
            - sub_units: 선택된 소단원들 (수학 1단원의 경우)
            - difficulty: 난이도
            - multiple_choice_count: 객관식 문제 수
            - subjective_count: 주관식 문제 수
            - question_types: 선택된 문제 유형들
    
    Returns:
        JSONResponse: 생성된 문제지 내용
    """
    try:
        # 입력값 검증
        if not settings:
            raise HTTPException(status_code=400, detail="설정 정보가 제공되지 않았습니다.")
        
        required_fields = ['subject', 'difficulty', 'multiple_choice_count', 'subjective_count']
        for field in required_fields:
            if field not in settings:
                raise HTTPException(status_code=400, detail=f"필수 필드 '{field}'가 누락되었습니다.")
        
        # 문제 수 검증
        total_problems = settings.get('multiple_choice_count', 0) + settings.get('subjective_count', 0)
        if total_problems == 0:
            raise HTTPException(status_code=400, detail="객관식과 주관식 문제 수의 합이 0이어야 합니다.")
        
        # 문제지 생성
        generated_problem = await handle_problem_generation(settings)
        
        if not generated_problem:
            raise HTTPException(status_code=500, detail="문제지 생성에 실패했습니다.")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "문제지가 성공적으로 생성되었습니다.",
                "data": {
                    "problem_content": generated_problem,
                    "settings_used": settings
                }
            }
        )
        
    except HTTPException as e:
        # HTTP 예외는 그대로 전달
        raise e
    except Exception as e:
        # 기타 예외는 500 에러로 처리
        print(f"문제지 생성 중 예상치 못한 오류 발생: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"문제지 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    문제 생성 서비스 상태 확인
    """
    return {"status": "healthy", "service": "problem-generation"} 