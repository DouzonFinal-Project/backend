from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone

def _now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def add_error_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # 필요시 로깅 추가 가능
        return JSONResponse(
            status_code=500,
            content={
                "error": {"code": "INTERNAL_ERROR", "message": str(exc)},
                "generated_at": _now_iso(),
                "latency_ms": 0,
            },
        )
