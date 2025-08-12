from schemas.llm import SummaryRequest, SummaryResponse, SearchRequest, SearchResponse
from schemas.common import make_meta

def summarize(req: SummaryRequest) -> SummaryResponse:
    text = (req.text or "").strip()
    # 아주 간단한 더미 요약
    summary = text[:200] + ("..." if len(text) > 200 else "")
    bullets = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()][:3]
    result = {"summary": summary, "bullets": bullets, "action_items": []}
    return SummaryResponse(result=result, tokens={"prompt": 0, "completion": 0}, meta=make_meta("llm"))

def hybrid_search(req: SearchRequest) -> SearchResponse:
    rdb_block = None
    vector_block = None
    if "rdb" in req.include:
        rdb_block = {
            "filters": {"student_id": req.student_id, "date_from": req.date_from, "date_to": req.date_to},
            "grades": {"avg": 0.0, "subjects": []}  # 더미
        }
    if "vector" in req.include:
        vector_block = {
            "query": req.q,
            "top_k": req.top_k,
            "matches": []  # 더미
        }
    return SearchResponse(rdb=rdb_block, vector=vector_block, meta=make_meta("hybrid"))
