from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import SessionLocal
from pydantic import BaseModel
from services.ai_service import process_ai_query

router = APIRouter(prefix="/ai", tags=["AI 챗봇"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)

async def chat_with_ai(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # AI 서비스 호출
        response = await process_ai_query(request.message, db)

        return ChatResponse(response=response)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 처리 중 오류가 발생했습니다: {str(e)}")

# 추가 AI 기능들을 위한 엔드포인트
@router.get("/health")

async def ai_health_check():
    return {"status": "AI 서비스 정상 작동 중"} 