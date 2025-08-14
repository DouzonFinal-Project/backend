"""
LLM 라우터
- 프론트엔드로부터 LLM 요청을 받아 Gemini API 호출
- mode: json | text
- task: 업무/프롬프트 태스크명
- prompt: 사용자 프롬프트
- options: temperature, max_tokens 등 파라미터 (선택)
"""

from fastapi import APIRouter, HTTPException, Response, Header, status
from pydantic import BaseModel, Field
from typing import Any, Optional
from services.llm.llm_gemini import generate_json, generate_text

router = APIRouter(tags=["LLM"])

# 요청 모델
class GenerateReq(BaseModel):
    mode: str = Field("json", pattern="^(json|text)$", description="응답 형식: json 또는 text")
    task: str = Field(..., description="태스크명(예: counseling_summary)")
    prompt: str = Field(..., description="사용자 프롬프트")
    options: Optional[dict] = Field(default=None, description='예: {"temperature":0.2,"max_tokens":600}')

# 응답 모델
class GenerateRes(BaseModel):
    ok: bool = True
    data: Any
    usage: Optional[dict] = None
    trace_id: Optional[str] = None

@router.post(
    "/generate",
    response_model=GenerateRes,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    summary="Gemini 호출(텍스트/JSON)",
    description="mode=json이면 JSON만 반환하도록 유도된 프롬프트로 호출합니다.",
)
async def post_generate(req: GenerateReq, response: Response,
                        x_request_id: str | None = Header(default=None, alias="X-Request-Id")):
    """
    LLM 요청 처리 엔드포인트
    - mode에 따라 JSON/텍스트 호출 분기
    - X-Request-Id를 응답 헤더로 전달(요청 추적)
    - Cache-Control: no-store (민감 데이터 캐싱 방지)
    """
    system = f"Task: {req.task}. Keep outputs concise for teachers."
    try:
        # mode에 따라 호출 분기
        if req.mode == "json":
            out = await generate_json(system, req.prompt, **(req.options or {}))
        else:
            out = await generate_text(system, req.prompt, **(req.options or {}))

        # 응답 헤더 처리
        if x_request_id:
            response.headers["X-Request-Id"] = x_request_id
        response.headers["Cache-Control"] = "no-store"

        return {"ok": True, "data": out["content"], "usage": out.get("usage")}
    except Exception as e:
        # LLM 호출 실패 시 502 반환
        raise HTTPException(502, f"Gemini 호출 실패: {e}")
