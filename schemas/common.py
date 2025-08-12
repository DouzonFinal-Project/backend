from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timezone

class MetaInfo(BaseModel):
    generated_at: str
    latency_ms: int
    source: str
    cache_hit: bool = False

class ErrorResponse(BaseModel):
    error: Dict[str, Any]
    generated_at: str
    latency_ms: int

class Pagination(BaseModel):
    page: int
    page_size: int
    total: Optional[int] = None
    next_cursor: Optional[str] = None

def make_meta(source: str, latency_ms: int = 0, cache_hit: bool = False) -> MetaInfo:
    return MetaInfo(
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        latency_ms=latency_ms,
        source=source,
        cache_hit=cache_hit,
    )