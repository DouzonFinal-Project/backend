from fastapi import APIRouter, Depends
from schemas.front_requests import ExampleFrontRequest
from schemas.front_responses import ExampleFrontResponse
from services.front_client import front_client

router = APIRouter(prefix="/front", tags=["Front API"])

# ==========================================================
# [PROXY] Front → Backend 연동 API
# - 프론트엔드에서 요청한 데이터를 서비스 레이어(front_client)로 전달
# - 서비스 레이어에서 가공된 데이터를 응답 형식에 맞춰 반환
# - 모든 응답은 success/data/error 구조로 통일
# ==========================================================

@router.post("/example")
def example_proxy(req: ExampleFrontRequest):
    try:
        # ✅ 서비스 레이어(front_client)를 호출하여 데이터 처리
        data = front_client.get_example_data(req.model_dump())

        # ✅ 성공 시 공통 응답 포맷으로 반환
        return {
            "success": True,
            "data": data,
            "message": "Front proxy request processed successfully"
        }

    except Exception as e:
        # ✅ 예외 발생 시 error 블록으로 감싸 반환
        return {
            "success": False,
            "error": {
                "code": 500,
                "message": f"Front proxy request failed: {str(e)}"
            }
        }
