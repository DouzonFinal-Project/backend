from typing import Optional, Annotated
from fastapi import Header, HTTPException
from config.settings import settings
import hmac

AuthHeader = Annotated[Optional[str], Header(alias="Authorization")]

def require_llm_token(authorization: AuthHeader = None):
    # 설정 누락 방지(선택): 환경에서 토큰이 비어있으면 개발 중 오류를 명확히 드러냄
    if not getattr(settings, "LLM_INTERNAL_TOKEN", None):
        raise HTTPException(status_code=500, detail="Server token not configured")

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # "Bearer <token>" 파싱
    try:
        scheme, token = authorization.split(" ", 1)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid auth scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 타이밍 안전 비교
    if not hmac.compare_digest(token.strip(), settings.LLM_INTERNAL_TOKEN):
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"client": "llm"}
