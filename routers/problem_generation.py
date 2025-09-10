from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, Any
import json

router = APIRouter(prefix="/problem-generation", tags=["problem-generation"])


@router.post("/generate-streaming")
async def generate_problem_set_streaming_endpoint(settings: Dict[str, Any]):
    """
    문제출제설정에 맞는 문제지를 진정한 실시간 스트리밍으로 생성합니다.
    
    Args:
        settings: 문제 출제 설정 정보
    
    Returns:
        StreamingResponse: 실시간 스트리밍으로 생성되는 문제지 내용
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
        
        # 스트리밍 문제지 생성
        from services.ai_handlers.problem_generator_handler import problem_generator_handler
        
        async def generate_stream():
            try:
                # 즉시 스트리밍 시작 신호 (Cursor처럼)
                yield f"data: {json.dumps({'type': 'start', 'message': '문제지 생성 시작'}, ensure_ascii=False)}\n\n"
                
                chunk_count = 0
                async for word in problem_generator_handler.generate_problem_set_streaming(settings):
                    if word and (word.strip() or word in ['\n', ' ', '\t']):
                        chunk_count += 1
                        # Cursor처럼 단어별 SSE 전송
                        yield f"data: {json.dumps({'chunk': word, 'type': 'content', 'chunk_id': chunk_count}, ensure_ascii=False)}\n\n"
                
                # 스트리밍 완료 신호
                yield f"data: {json.dumps({'type': 'done', 'message': '문제지 생성 완료', 'total_chunks': chunk_count}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                print(f"스트리밍 생성 중 오류: {e}")
                error_data = json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)
                yield f"data: {error_data}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",  # 올바른 SSE 미디어 타입
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream; charset=utf-8",
                "Access-Control-Allow-Origin": "*",  # CORS 지원
                "Access-Control-Allow-Headers": "Cache-Control",
                "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"스트리밍 문제지 생성 중 예상치 못한 오류 발생: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"스트리밍 문제지 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    문제 생성 서비스 상태 확인
    """
    return {"status": "healthy", "service": "problem-generation"} 