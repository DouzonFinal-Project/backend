from fastapi import APIRouter, HTTPException, Depends
from typing import List
from services.ai_client import ai_client, AIClientError
from schemas.ai_schemas import (
    CounselingRecordAdd, CounselingRecordSearch,
    CounselingChatRequest, QuickChatRequest,
    CounselingPlanRequest, ConversationSummaryRequest,
    KeywordExtractionRequest, AIResponse
)

router = APIRouter(prefix="/ai", tags=["AI 챗봇"])


# ===============================================================
# 상담 기록 관리 (Milvus)
# ===============================================================

@router.post("/counseling/records", response_model=AIResponse)
async def add_counseling_record(record: CounselingRecordAdd):
    """상담 기록 추가"""
    try:
        result = ai_client.add_counseling_record(**record.model_dump())
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/counseling/records/bulk", response_model=AIResponse)
async def bulk_add_counseling_records(records: List[CounselingRecordAdd]):
    """일괄 상담 기록 추가"""
    try:
        records_data = [record.model_dump() for record in records]
        result = ai_client.bulk_add_counseling_records(records_data)
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/counseling/records/search", response_model=AIResponse)
async def search_counseling_records(search: CounselingRecordSearch):
    """상담 기록 검색"""
    try:
        result = ai_client.search_counseling_records(**search.model_dump())
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/counseling/records/{record_id}", response_model=AIResponse)
async def delete_counseling_record(record_id: int):
    """상담 기록 삭제"""
    try:
        result = ai_client.delete_counseling_record(record_id)
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/counseling/collection-stats", response_model=AIResponse)
async def get_collection_stats():
    """벡터 DB 통계 조회"""
    try:
        result = ai_client.get_collection_stats()
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===============================================================
# AI 채팅 (Gemini)
# ===============================================================

@router.post("/chat/counseling", response_model=AIResponse)
async def counseling_chat(request: CounselingChatRequest):
    """전문 상담 채팅 (RAG 지원)"""
    try:
        # ConversationMessage를 dict로 변환
        conversation_history = None
        if request.conversation_history:
            conversation_history = [msg.model_dump() for msg in request.conversation_history]
        
        request_data = request.model_dump()
        request_data["conversation_history"] = conversation_history
        
        result = ai_client.counseling_chat(**request_data)
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/quick", response_model=AIResponse)
async def quick_chat(request: QuickChatRequest):
    """간단 채팅 (RAG 없이)"""
    try:
        # ConversationMessage를 dict로 변환
        conversation_history = None
        if request.conversation_history:
            conversation_history = [msg.model_dump() for msg in request.conversation_history]
        
        request_data = request.model_dump()
        request_data["conversation_history"] = conversation_history
        
        result = ai_client.quick_chat(**request_data)
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/counseling/plan", response_model=AIResponse)
async def create_counseling_plan(request: CounselingPlanRequest):
    """개별 상담 계획 수립"""
    try:
        result = ai_client.create_counseling_plan(**request.model_dump())
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation/summarize", response_model=AIResponse)
async def summarize_conversation(request: ConversationSummaryRequest):
    """대화 내용 요약"""
    try:
        # ConversationMessage를 dict로 변환
        conversation_history = [msg.model_dump() for msg in request.conversation_history]
        
        request_data = request.model_dump()
        request_data["conversation_history"] = conversation_history
        
        result = ai_client.summarize_conversation(**request_data)
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text/extract-keywords", response_model=AIResponse)
async def extract_keywords(request: KeywordExtractionRequest):
    """키워드 추출"""
    try:
        result = ai_client.extract_keywords(**request.model_dump())
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===============================================================
# 가이드 및 템플릿 조회
# ===============================================================

@router.get("/templates", response_model=AIResponse)
async def get_chat_templates():
    """상담 템플릿 조회"""
    try:
        result = ai_client.get_chat_templates()
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guidelines", response_model=AIResponse)
async def get_counseling_guidelines():
    """상담 가이드라인 조회"""
    try:
        result = ai_client.get_counseling_guidelines()
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===============================================================
# 시스템 상태 및 통계
# ===============================================================

@router.get("/status", response_model=AIResponse)
async def get_ai_service_status():
    """AI 서비스 상태 확인"""
    try:
        result = ai_client.get_service_status()
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=AIResponse)
async def get_usage_statistics():
    """사용 통계 조회"""
    try:
        result = ai_client.get_usage_statistics()
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=AIResponse)
async def ai_health_check():
    """AI 서버 헬스체크"""
    try:
        result = ai_client.health_check()
        return AIResponse(status="success", data=result)
    except AIClientError as e:
        raise HTTPException(status_code=500, detail=str(e))