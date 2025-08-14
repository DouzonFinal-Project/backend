from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# Milvus 관련 스키마
class CounselingRecordAdd(BaseModel):
    student_query: str = Field(..., description="학생 문의 내용")
    counselor_answer: str = Field(..., description="상담 답변")
    date: str = Field(..., description="상담 날짜 (YYYY-MM-DD)")
    title: Optional[str] = Field(None, description="상담 제목")
    teacher_name: Optional[str] = Field(None, description="상담 교사명")
    student_name: Optional[str] = Field(None, description="학생명")
    worry_tags: Optional[str] = Field(None, description="고민 태그")


class CounselingRecordSearch(BaseModel):
    query: str = Field(..., description="검색 쿼리")
    top_k: int = Field(5, ge=1, le=20, description="검색 결과 수")
    worry_tag: Optional[str] = Field(None, description="고민 태그 필터")


class SearchResult(BaseModel):
    id: int
    title: Optional[str]
    student_query: str
    counselor_answer: str
    date: str
    teacher_name: Optional[str]
    student_name: Optional[str]
    worry_tags: Optional[str]
    similarity: float


# Gemini 채팅 관련 스키마
class ConversationMessage(BaseModel):
    role: str = Field(..., description="user 또는 assistant")
    content: str = Field(..., description="메시지 내용")
    timestamp: Optional[str] = Field(None, description="메시지 시간")


class CounselingChatRequest(BaseModel):
    query: str = Field(..., description="상담 질문")
    use_rag: bool = Field(True, description="RAG 사용 여부")
    search_top_k: int = Field(3, ge=1, le=10, description="RAG 검색 결과 수")
    worry_tag_filter: Optional[str] = Field(None, description="고민 태그 필터")
    conversation_history: Optional[List[ConversationMessage]] = Field(None, description="대화 기록")
    student_name: Optional[str] = Field(None, description="학생명")
    context_info: Optional[Dict[str, str]] = Field(None, description="추가 상황 정보")


class QuickChatRequest(BaseModel):
    query: str = Field(..., description="질문")
    conversation_history: Optional[List[ConversationMessage]] = Field(None, description="대화 기록")
    urgency_level: str = Field("normal", description="긴급도 (low/normal/high/urgent)")


class CounselingPlanRequest(BaseModel):
    student_name: str = Field(..., description="학생명")
    grade: int = Field(..., ge=1, le=6, description="학년")
    main_concerns: List[str] = Field(..., description="주요 고민사항")
    current_situation: str = Field(..., description="현재 상황")
    family_background: Optional[str] = Field(None, description="가정 배경")
    academic_level: Optional[str] = Field(None, description="학업 수준 (high/medium/low)")
    social_skills: Optional[str] = Field(None, description="사회성 수준")


class ConversationSummaryRequest(BaseModel):
    conversation_history: List[ConversationMessage] = Field(..., description="대화 기록")
    include_action_items: bool = Field(True, description="실행 항목 포함 여부")
    summary_type: str = Field("detailed", description="요약 유형 (brief/detailed/formal)")


class KeywordExtractionRequest(BaseModel):
    text: str = Field(..., description="키워드 추출할 텍스트")
    include_priority: bool = Field(True, description="우선순위 포함 여부")
    extract_emotions: bool = Field(False, description="감정 추출 여부")


# 공통 응답 스키마
class AIResponse(BaseModel):
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None


class CounselingChatResponse(BaseModel):
    status: str
    response: str
    timestamp: str
    used_rag: bool
    search_results_count: int
    search_results: Optional[List[Dict[str, Any]]] = None
    context_quality: Optional[Dict[str, Any]] = None
    response_time: float