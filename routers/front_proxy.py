from fastapi import APIRouter, Depends, HTTPException
from schemas.front_requests import ExampleFrontRequest
from schemas.front_responses import ExampleFrontResponse
from services.front_client import front_client

router = APIRouter(prefix="/v1/front", tags=["Front API"])

@router.post("/example", response_model=ExampleFrontResponse)
def example_proxy(req: ExampleFrontRequest):
    try:
        data = front_client.get_example_data(req.dict())
        return ExampleFrontResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
