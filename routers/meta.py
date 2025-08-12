from fastapi import APIRouter
from schemas.common import make_meta

router = APIRouter(prefix="/meta", tags=["Meta"])

@router.get("/health")
def health():
    return {"status": "ok", "meta": make_meta("meta")}

@router.get("/limits")
def limits():
    return {
        "page_size_default": 50,
        "page_size_max": 200,
        "date_range_months_max": 12,
        "meta": make_meta("meta"),
    }