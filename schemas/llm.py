from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
from schemas.common import MetaInfo

# ✅ 요약 요청/응답 (POST /llm/summary)
class SummaryRequest(BaseModel):
    text: str
    task: Literal["summary", "bullets", "action_items", "custom"] = "summary"
    schema: Optional[Dict[str, Any]] = None         # 원하는 출력 스키마(JSON Schema 등)
    constraints: Optional[Dict[str, Any]] = None    # max_tokens, language 등 제약

class SummaryResponse(BaseModel):
    result: Dict[str, Any]                          # {"summary": "...", "bullets":[...], ...}
    tokens: Dict[str, int] = {"prompt": 0, "completion": 0}
    meta: MetaInfo                                   # 공통 메타(생성시각/latency/source/cache)

# ✅ 검색 요청/응답 (POST /llm/search)
#    ※ LLM은 JSON 본문으로만 통신하기로 했으므로 GET 대신 POST 바디 사용
class SearchRequest(BaseModel):
    q: str                                           # 자연어 질의
    student_id: Optional[int] = None
    date_from: Optional[str] = None                  # "YYYY-MM-DD"
    date_to: Optional[str] = None
    top_k: int = Field(5, ge=1, le=50)
    include: List[Literal["rdb", "vector"]] = ["rdb", "vector"]
    filters: Optional[Dict[str, Any]] = None         # doc_type, grade 등 메타 필터

class SearchResponse(BaseModel):
    rdb: Optional[Dict[str, Any]] = None             # 예: 성적/출결 요약 블록
    vector: Optional[Dict[str, Any]] = None          # 예: 매치 청크 리스트
    meta: MetaInfo

# (선택) 라우팅 의사결정 (POST /llm/route) 필요 시 사용
class RouteRequest(BaseModel):
    query: str
    hints: Optional[Dict[str, Any]] = None

class RouteResponse(BaseModel):
    route: Literal["rdb", "vector", "hybrid", "unknown"]
    reason: str
    meta: MetaInfo
