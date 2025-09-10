# routers/gemini.py

import os
import re

from typing import List, Optional, Dict, Any, Annotated, Union
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi import BackgroundTasks
from pydantic import BaseModel, Field
from functools import lru_cache
import json
import asyncio
import logging
from pymilvus import utility

from services.gemini_service import gemini_service
from routers.milvus import SearchRecordsRequest, get_milvus_collection

router = APIRouter()

logger = logging.getLogger(__name__)

# =========================
# Pydantic 모델 정의
# =========================

class ChatMessage(BaseModel):
    role: Annotated[str, Field(pattern="^(user|assistant)$")]
    content: Annotated[str, Field(min_length=1, max_length=10000)]
    timestamp: Optional[str] = None

class CounselingChatRequest(BaseModel):
    """상담 채팅 요청 모델"""
    query: Annotated[str, Field(min_length=1, max_length=2000, description="상담 질문")]
    use_rag: bool = Field(default=True, description="RAG 검색 사용 여부")
    search_top_k: Annotated[int, Field(default=3, ge=1, le=10)] = 3
    worry_tag_filter: Optional[str] = Field(default=None, max_length=100, description="검색시 고민 태그 필터")
    conversation_history: Optional[List[ChatMessage]] = Field(default=None, description="대화 히스토리 (최대 20개)")
    student_name: Optional[str] = Field(default=None, max_length=50, description="학생 이름 (선택)")
    context_info: Optional[Dict[str, str]] = Field(default=None, description="추가 상황 정보")

class QuickChatRequest(BaseModel):
    """간단 채팅 요청 (RAG 없이)"""
    query: Annotated[str, Field(min_length=1, max_length=2000)]
    conversation_history: Optional[List[ChatMessage]] = None
    urgency_level: Optional[str] = Field(default="normal", pattern="^(low|normal|high|urgent)$")

class SummarizeRequest(BaseModel):
    """대화 요약 요청"""
    conversation_history: List[ChatMessage] = Field(min_items=2, max_items=50)
    include_action_items: bool = Field(default=True, description="실행 계획 포함 여부")
    summary_type: str = Field(default="detailed", pattern="^(brief|detailed|formal)$")

class ExtractKeywordsRequest(BaseModel):
    """키워드 추출 요청"""  
    text: Annotated[str, Field(min_length=10, max_length=5000)]
    include_priority: bool = Field(default=True, description="우선순위 정보 포함")
    extract_emotions: bool = Field(default=False, description="감정 상태 분석 포함")

class CounselingPlanRequest(BaseModel):
    """상담 계획 수립 요청"""
    query: Annotated[str, Field(min_length=1, max_length=2000, description="상담 질문")]
    use_rag: bool = Field(default=True, description="RAG 검색 사용 여부")
    search_top_k: Annotated[int, Field(default=3, ge=1, le=10)] = 3
    worry_tag_filter: Optional[str] = Field(default=None, max_length=100, description="검색시 고민 태그 필터")
    conversation_history: Optional[List[ChatMessage]] = Field(default=None, description="대화 히스토리 (최대 20개)")
    student_name: Optional[str] = Field(default=None, max_length=50, description="학생 이름 (선택)")
    context_info: Optional[Dict[str, str]] = Field(default=None, description="추가 상황 정보")

class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    status: str
    response: Optional[str] = None
    error: Optional[str] = None
    timestamp: str
    used_rag: Optional[bool] = None
    search_results_count: Optional[int] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    context_quality: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None

class MasterChatRequest(BaseModel):
    # 단일 액션만 허용. 없으면 자동판단 -> counseling_chat
    action: Optional[str] = Field(default=None, description="요청 액션 (optional). 허용값: counseling_chat, quick_chat, counseling_plan, summarize, extract_keywords")
    query: Optional[str] = Field(default=None, description="사용자 쿼리 / 질문 (대부분 필수)")
    use_rag: bool = Field(default=True, description="RAG 사용 여부 (counseling_chat일 때 주로 사용)")
    search_top_k: int = Field(default=3, ge=1, le=10, description="RAG 검색 상위 k")
    worry_tag_filter: Optional[str] = Field(default=None, description="RAG 검색시 고민 태그 필터")
    conversation_history: Optional[list] = Field(default=None, description="대화 히스토리 (ChatMessage list)")
    student_name: Optional[str] = Field(default=None, description="학생 이름 (선택)")
    context_info: Optional[Dict[str, str]] = Field(default=None, description="추가 상황 정보 (선택)")
    urgency_level: Optional[str] = Field(default="normal", description="quick_chat 전용: low|normal|high|urgent")
    extract_text: Optional[str] = Field(default=None, description="extract_keywords 전용: 추출 대상 텍스트")
    plan_payload: Optional[Dict[str, Any]] = Field(default=None, description="counseling_plan 전용: 학생정보 등")
    stream: bool = Field(default=False, description="스트리밍 모드 (현재 미지원; 추후 활성화 예정)")

# =========================
# 개선된 RAG 검색 함수
# =========================

async def perform_rag_search_unified(
    query: str, 
    top_k: int = 3, 
    worry_tag: Optional[str] = None,
    student_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    통합된 RAG 검색 함수 - 모든 액션에서 공통 사용
    """
    try:
        collection = get_milvus_collection()

        # 컬렉션 로드 상태 확인 및 로드
        is_loaded = await _ensure_collection_loaded(collection)
        if not is_loaded:
            logger.warning("Milvus collection 로드 실패")
            return []

        # 임베딩 생성
        embedding = await _generate_embedding(query)
        if not embedding:
            logger.error("임베딩 생성 실패")
            return []

        # 검색 쿼리 최적화 (학생 이름 포함)
        enhanced_query = query
        if student_name:
            enhanced_query = f"{student_name} 학생 {query}"

        # 검색 표현식 생성
        search_expr = _build_search_expression(worry_tag, student_name)

        # 검색 실행
        search_results = await _execute_search(
            collection, 
            embedding, 
            top_k, 
            search_expr
        )

        # 결과 처리 및 반환
        return _process_search_results(search_results, top_k)

    except Exception as e:
        logger.exception(f"통합 RAG 검색 실패: {e}")
        return []

async def _ensure_collection_loaded(collection) -> bool:
    """컬렉션 로드 상태 확인 및 로드"""
    try:
        load_state = utility.load_state(collection.name)
        if hasattr(load_state, "name"):
            is_loaded = load_state.name.lower() == "loaded"
        else:
            is_loaded = "loaded" in str(load_state).lower()

        if not is_loaded:
            collection.load()
            # 로드 완료 대기
            for _ in range(10):
                try:
                    load_state = utility.load_state(collection.name)
                    if (hasattr(load_state, "name") and load_state.name.lower() == "loaded") or \
                       ("loaded" in str(load_state).lower()):
                        return True
                except Exception:
                    pass
                await asyncio.sleep(0.2)
        
        return is_loaded
    except Exception as e:
        logger.error(f"컬렉션 로드 상태 확인 실패: {e}")
        return False

async def _generate_embedding(query: str):
    """임베딩 생성"""
    try:
        from routers.milvus import embeddings
        emb_result = embeddings.aembed_query(query)
        
        if asyncio.iscoroutine(emb_result):
            embedding = await emb_result
        else:
            embedding = emb_result
        
        return list(embedding) if embedding is not None else None
    except Exception as e:
        logger.error(f"임베딩 생성 실패: {e}")
        return None

def _build_search_expression(worry_tag: Optional[str], student_name: Optional[str]) -> Optional[str]:
    """검색 표현식 생성 - worry_tags는 VARCHAR 필드"""
    expressions = []
    
    # worry_tag 필터링 (VARCHAR 필드이므로 LIKE 연산 사용)
    if worry_tag:
        if isinstance(worry_tag, (list, tuple)):
            raw_tags = [str(t).strip() for t in worry_tag if str(t).strip()]
        else:
            raw = str(worry_tag).strip()
            raw_tags = [t.strip() for t in re.split(r'[,/|;\s]+', raw) if t.strip()]

        if raw_tags:
            # 따옴표 제거 등 sanitize
            clean_tags = [t.replace('"', '').replace("'", "") for t in raw_tags]
            tag_clauses = [f'worry_tags like "%{tag}%"' for tag in clean_tags]
            expressions.append("(" + " or ".join(tag_clauses) + ")")
    
    # student_name 필터링 (정확한 매치)
    if student_name:
        clean_name = student_name.replace('"', '').replace("'", "")
        expressions.append(f'student_name == "{clean_name}"')
    
    return " and ".join(expressions) if expressions else None

async def _execute_search(collection, embedding: List[float], top_k: int, expr: Optional[str]) -> List:
    """검색 실행"""
    try:
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        
        loop = asyncio.get_running_loop()
        logger.debug(f"RAG 검색 실행 - expr: {expr}, top_k: {top_k}")
        
        results = await loop.run_in_executor(
            None,
            lambda: collection.search(
                data=[embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k * 2,  # 필터링을 고려해 더 많이 가져옴
                expr=expr,
                output_fields=["id", "title", "student_query", "counselor_answer", 
                             "date", "teacher_name", "student_name", "worry_tags"],
            )
        )
        
        return results[0] if results else []
    except Exception as e:
        logger.error(f"검색 실행 실패: {e}")
        return []

def _process_search_results(hits: List, top_k: int) -> List[Dict[str, Any]]:
    """검색 결과 처리"""
    if not hits:
        return []

    output = []
    
    # 1차: 임계값(>=0.2) 적용
    for hit in hits:
        try:
            similarity = round(1 - hit.distance, 4)
        except Exception:
            similarity = getattr(hit, "score", 0.0)

        if similarity >= 0.2:
            entity = getattr(hit, "entity", {}) or {}
            if not entity:
                try:
                    entity = hit.raw or {}
                except Exception:
                    entity = {}

            result = {
                "id": entity.get("id"),
                "title": entity.get("title"),
                "student_query": entity.get("student_query"),
                "counselor_answer": entity.get("counselor_answer"),
                "date": entity.get("date"),
                "teacher_name": entity.get("teacher_name"),
                "student_name": entity.get("student_name"),
                "worry_tags": entity.get("worry_tags"),
                "similarity": similarity,
            }
            output.append(result)
            if len(output) >= top_k:
                break

    # 2차: 결과가 없으면 임계값 무시하고 top_k개 반환
    if not output and hits:
        logger.debug("임계값 조건 미충족 - 상위 결과로 폴백")
        for hit in hits[:top_k]:
            try:
                similarity = round(1 - hit.distance, 4)
            except Exception:
                similarity = getattr(hit, "score", 0.0)

            entity = getattr(hit, "entity", {}) or {}
            if not entity:
                try:
                    entity = hit.raw or {}
                except Exception:
                    entity = {}

            result = {
                "id": entity.get("id"),
                "title": entity.get("title"),
                "student_query": entity.get("student_query"),
                "counselor_answer": entity.get("counselor_answer"),
                "date": entity.get("date"),
                "teacher_name": entity.get("teacher_name"),
                "student_name": entity.get("student_name"),
                "worry_tags": entity.get("worry_tags"),
                "similarity": similarity,
            }
            output.append(result)

    return output

# =========================
# 공통 RAG 처리 함수
# =========================

async def execute_rag_search_for_action(
    action: str,
    request_data: Dict[str, Any]
) -> tuple[List[Dict[str, Any]], bool]:
    """
    액션별로 RAG 검색을 실행하고 결과를 반환
    Returns: (search_results, used_rag)
    """
    # RAG 사용 조건 확인
    use_rag = request_data.get('use_rag', True)
    query = request_data.get('query')
    
    # RAG를 사용하는 액션들
    rag_enabled_actions = {'counseling_chat', 'counseling_plan'}
    
    if not use_rag or action not in rag_enabled_actions or not query:
        return [], False
    
    try:
        search_query = query
        student_name = request_data.get('student_name')
        if student_name:
            search_query = f"{student_name} 학생 {query}"
            
        search_results = await perform_rag_search_unified(
            query=search_query,
            top_k=request_data.get('search_top_k', 3),
            worry_tag=request_data.get('worry_tag_filter'),
            student_name=student_name
        )
        
        logger.info(f"RAG 검색 완료 ({action}): {len(search_results)}개 결과")
        return search_results, bool(search_results)
        
    except Exception as e:
        logger.exception(f"RAG 검색 실패 ({action}): {e}")
        return [], False

def log_conversation(query: str, response: str, used_rag: bool, search_count: int):
    """대화 로그 기록 (백그라운드 태스크)"""
    try:
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "query_length": len(query),
            "response_length": len(response),
            "used_rag": used_rag,
            "search_results_count": search_count,
        }
        logger.info(f"대화 로그: {json.dumps(log_data, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"로그 기록 실패: {e}")

# =========================
# templates
# =========================
@lru_cache(maxsize=1)
def _load_json_data(filename: str) -> Dict[str, Any]:
    """템플릿 폴더에서 JSON 파일을 읽어옵니다. 캐싱을 적용하여 효율성을 높입니다."""
    file_path = os.path.join(os.path.dirname(__file__), '..', 'templates', filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"'{filename}' 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
        raise HTTPException(status_code=500, detail="서버 템플릿 파일을 찾을 수 없습니다.")
    
@router.get("/chat-templates/")
async def get_chat_templates():
    """자주 사용되는 상담 질문 템플릿 제공"""
    templates = _load_json_data("chat_templates.json")
    
    return {
        "status": "success",
        "templates": templates,
        "total_categories": len(templates),
        "total_templates": sum(len(v["templates"]) for v in templates.values()),
        "usage_tip": "상황에 맞는 템플릿을 선택하거나 참고하여 구체적인 질문을 작성해보세요."
    }

@router.get("/counseling-guidelines/")
async def get_counseling_guidelines():
    """초등학교 상담 가이드라인 제공"""
    data = _load_json_data("counseling_guidelines.json")
    
    # JSON 파일의 루트에 있는 'guidelines'와 기타 필드를 직접 반환
    return {
        "status": "success",
        **data
    }

# =========================
# API 엔드포인트
# =========================

@router.post("/master-chat/", response_model=ChatResponse)
async def master_chat(request: MasterChatRequest, background_tasks: BackgroundTasks):
    """
    Master router (single-action mode).
    - action이 지정되지 않으면 query 텍스트 기반 자동판단 후 처리.
    - 반환: 기존 ChatResponse 형태 (response: str) — 응답은 순수 텍스트.
    """
    start_time = datetime.now()

    # 허용 액션 목록
    allowed = {"counseling_chat", "quick_chat", "counseling_plan", "summarize", "extract_keywords"}

    # 1) action 결정: 우선 request.action(있으면 검증), 없으면 키워드 자동판단
    action = (request.action or "").strip() or None
    if action and action not in allowed:
        raise HTTPException(status_code=400, detail=f"unsupported action: {action}")

    # 자동판단 로직 (action 미지정)
    if not action:
        q = (request.query or "").lower()
        if any(k in q for k in ["계획", "계획 수립", "상담 계획", "plan 작성", "plan"]):
            action = "counseling_plan"
        elif any(k in q for k in ["요약", "정리", "요약해", "summarize", "summary"]):
            action = "summarize"
        elif any(k in q for k in ["키워드", "태그", "핵심어", "추출"]):
            action = "extract_keywords"
        elif any(k in q for k in ["긴급", "급함", "빨리", "빠른"]):
            action = "quick_chat"
        else:
            action = "counseling_chat"  # 기본

    # 필수 필드 검증
    if action in {"counseling_chat", "quick_chat", "counseling_plan"} and not request.query:
        raise HTTPException(status_code=400, detail="query is required for chat actions")
    if action == "summarize" and not request.conversation_history:
        raise HTTPException(status_code=400, detail="conversation_history is required for summarize")
    if action == "extract_keywords" and not (request.extract_text or request.query or request.conversation_history):
        raise HTTPException(status_code=400, detail="Need text (extract_text or query or conversation_history) to extract keywords")

    # 2) 통합 RAG 검색 실행
    request_dict = {
        'use_rag': request.use_rag,
        'query': request.query,
        'search_top_k': request.search_top_k,
        'worry_tag_filter': request.worry_tag_filter,
        'student_name': request.student_name
    }
    
    search_results, used_rag = await execute_rag_search_for_action(action, request_dict)

    # 3) 대화 히스토리/컨텍스트 준비 (기존과 동일하게 최근 일부만 사용)
    conversation_history = None
    if request.conversation_history:
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history[-20:]
        ]

    # 4) 추가 컨텍스트 포함한 쿼리 (기존 counseling_chat의 enhanced_query 방식 재사용)
    enhanced_query = request.query or ""
    if request.context_info:
        parts = [f"{k}: {v}" for k, v in request.context_info.items()]
        if parts:
            enhanced_query = f"{enhanced_query}\n\n[추가 상황 정보]\n" + "\n".join(parts)

    # 5) 스트리밍 처리(현재 미지원)
    if request.stream:
        raise HTTPException(status_code=501, detail="streaming mode is not implemented yet. Will add a streaming generator in gemini_service and then enable this flag.")

    # 6) 액션별 실행 (단일 액션)
    try:
        if action == "counseling_chat":
            result = await gemini_service.generate_counseling_response(
                user_query=enhanced_query,
                search_results=search_results if used_rag else None,
                conversation_history=conversation_history
            )
            if result.get("status") == "success":
                # 비동기 로깅(기존 방식 재사용)
                background_tasks.add_task(log_conversation, request.query or "", result["response"], used_rag, len(search_results))
                response_time = (datetime.now() - start_time).total_seconds()
                return ChatResponse(
                    status="success",
                    response=result["response"],
                    timestamp=result.get("timestamp", datetime.now().isoformat()),
                    used_rag=used_rag,
                    search_results_count=len(search_results) if used_rag else 0,
                    response_time=response_time
                )
            else:
                raise HTTPException(status_code=500, detail=result.get("error", "counseling generation failed"))

        elif action == "quick_chat":
            q = enhanced_query
            if request.urgency_level == "urgent":
                q = f"[긴급 상담] {q}\n\n즉시 실행 가능한 구체적 해결책을 우선 제시해주세요."
            elif request.urgency_level == "high":
                q = f"[우선 처리] {q}\n\n빠른 해결이 필요합니다."

            result = await gemini_service.generate_counseling_response(
                user_query=q, search_results=None, conversation_history=conversation_history
            )
            if result.get("status") == "success":
                response_time = (datetime.now() - start_time).total_seconds()
                return ChatResponse(
                    status="success",
                    response=result["response"],
                    timestamp=result.get("timestamp", datetime.now().isoformat()),
                    used_rag=False,
                    search_results_count=0,
                    response_time=response_time
                )
            else:
                raise HTTPException(status_code=500, detail=result.get("error", "quick chat failed"))

        elif action == "summarize":
            # generate_summary expects conversation_history list
            result = await gemini_service.generate_summary(conversation_history)
            if isinstance(result, dict) and result.get("status") == "success":
                response_time = (datetime.now() - start_time).total_seconds()
                return ChatResponse(
                    status="success",
                    response=result.get("summary"),
                    timestamp=result.get("timestamp", datetime.now().isoformat()),
                    used_rag=False,
                    search_results_count=0,
                    response_time=response_time
                )
            else:
                raise HTTPException(status_code=500, detail=result.get("error", "summary generation failed"))

        elif action == "extract_keywords":
            # 우선 extract_text -> query -> conversation_history 순으로 텍스트 확보
            text_for_extract = request.extract_text or request.query or ""
            if not text_for_extract and conversation_history:
                text_for_extract = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_history])
            result = await gemini_service.generate_keywords(text_for_extract)
            if isinstance(result, dict) and result.get("status") == "success":
                response_time = (datetime.now() - start_time).total_seconds()
                return ChatResponse(
                    status="success",
                    response=result.get("keywords"),
                    timestamp=result.get("timestamp", datetime.now().isoformat()),
                    used_rag=False,
                    search_results_count=0,
                    response_time=response_time
                )
            else:
                raise HTTPException(status_code=500, detail=result.get("error", "keyword extraction failed"))

        elif action == "counseling_plan":
            # student_info 구성
            student_info = {
                "student_name": request.student_name or "해당 학생", 
                "query": request.query,
                "grade": 6,  # 기본값
                "main_concerns": [],
                "current_situation": request.query,
            }
            
            # plan_payload나 context_info에서 추가 정보 추출
            if request.plan_payload:
                student_info.update(request.plan_payload)
            elif request.context_info:
                for key, value in request.context_info.items():
                    if key in ["grade", "main_concerns", "current_situation", "student_name"]:
                        student_info[key] = value

            # worry_tag_filter를 main_concerns로 활용
            if request.worry_tag_filter:
                concerns = [tag.strip() for tag in re.split(r'[,/|;\s]+', request.worry_tag_filter) if tag.strip()]
                student_info["main_concerns"] = concerns

            result = await gemini_service.generate_counseling_plan(
                student_info=student_info,
                search_results=search_results  # RAG 결과 전달
            )
            
            if isinstance(result, dict) and result.get("status") == "success":
                # 백그라운드 로깅
                background_tasks.add_task(
                    log_conversation,
                    f"상담계획 수립: {request.student_name or '익명'} - {request.query[:100]}",
                    result.get("counseling_plan", "")[:200] + "...",
                    used_rag,
                    len(search_results)
                )
                
                response_time = (datetime.now() - start_time).total_seconds()
                return ChatResponse(
                    status="success",
                    response=result.get("counseling_plan"),
                    timestamp=result.get("timestamp", datetime.now().isoformat()),
                    used_rag=used_rag,
                    search_results_count=len(search_results) if used_rag else 0,
                    response_time=response_time
                )
            else:
                raise HTTPException(status_code=500, detail=result.get("error", "counseling plan generation failed"))

        else:
            raise HTTPException(status_code=400, detail=f"unsupported action: {action}")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("master-chat failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/counseling-chat/", response_model=ChatResponse)
async def counseling_chat(request: CounselingChatRequest, background_tasks: BackgroundTasks):
    """전문 상담 채팅 (RAG 지원)"""
    start_time = datetime.now()
    
    try:
        # 통합 RAG 검색 사용
        request_dict = {
            'use_rag': request.use_rag,
            'query': request.query,
            'search_top_k': request.search_top_k,
            'worry_tag_filter': request.worry_tag_filter,
            'student_name': request.student_name
        }
        
        search_results, used_rag = await execute_rag_search_for_action('counseling_chat', request_dict)
        
        # 대화 히스토리 변환
        conversation_history = None
        if request.conversation_history:
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history[-20:]  # 최근 20개만
            ]
        
        # 추가 컨텍스트 정보 처리
        enhanced_query = request.query
        if request.context_info:
            context_parts = []
            for key, value in request.context_info.items():
                context_parts.append(f"{key}: {value}")
            if context_parts:
                enhanced_query = f"{request.query}\n\n[추가 상황 정보]\n" + "\n".join(context_parts)
        
        # Gemini API 호출
        result = await gemini_service.generate_counseling_response(
            user_query=enhanced_query,
            search_results=search_results,
            conversation_history=conversation_history
        )
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        if result["status"] == "success":
            # 백그라운드에서 로그 기록
            background_tasks.add_task(
                log_conversation, 
                request.query, 
                result["response"], 
                used_rag, 
                len(search_results)
            )
            
            return ChatResponse(
                status="success",
                response=result["response"],
                timestamp=result["timestamp"],
                used_rag=used_rag,
                search_results_count=len(search_results),
                search_results=search_results if used_rag else None,
                context_quality=result.get("context_quality"),
                response_time=response_time
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    
    except Exception as e:
        logger.exception("상담 채팅 처리 실패")
        raise HTTPException(status_code=500, detail=f"상담 채팅 처리 실패: {str(e)}")


@router.post("/quick-chat/", response_model=ChatResponse)
async def quick_chat(request: QuickChatRequest):
    """간단 채팅 (RAG 없이)"""
    start_time = datetime.now()
    
    try:
        # 긴급도에 따른 쿼리 강화
        enhanced_query = request.query
        if request.urgency_level == "urgent":
            enhanced_query = f"[긴급 상담] {request.query}\n\n즉시 실행 가능한 구체적인 해결책을 우선 제시해주세요."
        elif request.urgency_level == "high":
            enhanced_query = f"[우선 처리] {request.query}\n\n빠른 해결이 필요한 상황입니다."
        
        # 대화 히스토리 변환
        conversation_history = None
        if request.conversation_history:
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history[-10:]  # 최근 10개만
            ]
        
        # Gemini API 호출 (RAG 없이)
        result = await gemini_service.generate_counseling_response(
            user_query=enhanced_query,
            search_results=None,  # RAG 사용 안함
            conversation_history=conversation_history
        )
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        if result["status"] == "success":
            return ChatResponse(
                status="success",
                response=result["response"],
                timestamp=result["timestamp"],
                used_rag=False,
                search_results_count=0,
                response_time=response_time
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    
    except Exception as e:
        logger.exception("간단 채팅 처리 실패")
        raise HTTPException(status_code=500, detail=f"간단 채팅 처리 실패: {str(e)}")


@router.post("/counseling-plan/", response_model=ChatResponse)
async def create_counseling_plan(request: CounselingPlanRequest, background_tasks: BackgroundTasks):
    """개별 학생을 위한 상담 계획 수립 (RAG 검색 결과 기반)"""
    start_time = datetime.now()

    try:
        # 통합 RAG 검색 사용
        request_dict = {
            'use_rag': request.use_rag,
            'query': request.query,
            'search_top_k': request.search_top_k,
            'worry_tag_filter': request.worry_tag_filter,
            'student_name': request.student_name
        }
        
        search_results, used_rag = await execute_rag_search_for_action('counseling_plan', request_dict)

        # 학생 정보 구성
        student_info = {
            "student_name": request.student_name or "해당 학생",
            "query": request.query,
            "grade": 6,  # 기본값, 추후 request에서 받도록 확장 가능
            "main_concerns": [],  # worry_tag_filter에서 추출 가능
            "current_situation": request.query,
        }
        
        # context_info가 있으면 student_info에 병합
        if request.context_info:
            for key, value in request.context_info.items():
                if key in ["grade", "main_concerns", "current_situation"]:
                    student_info[key] = value
                elif key == "concerns":
                    student_info["main_concerns"] = value.split(",") if isinstance(value, str) else value

        # worry_tag_filter가 있으면 main_concerns로 활용
        if request.worry_tag_filter:
            if isinstance(request.worry_tag_filter, str):
                concerns = [tag.strip() for tag in re.split(r'[,/|;\s]+', request.worry_tag_filter) if tag.strip()]
            else:
                concerns = request.worry_tag_filter
            student_info["main_concerns"] = concerns

        logger.info(f"상담 계획 수립 시작 - 학생: {student_info['student_name']}, RAG 사용: {used_rag}, 결과 수: {len(search_results)}")

        # 상담 계획 생성
        result = await gemini_service.generate_counseling_plan(
            student_info=student_info,
            search_results=search_results  # RAG 결과 전달
        )
        
        response_time = (datetime.now() - start_time).total_seconds()

        # 성공 응답 반환
        if result.get("status") == "success":
            # 백그라운드 로깅
            background_tasks.add_task(
                log_conversation,
                f"상담계획 수립: {request.student_name or '익명'} - {request.query[:100]}",
                result.get("counseling_plan", "")[:200] + "...",
                used_rag,
                len(search_results)
            )
            
            return ChatResponse(
                status="success",
                response=result["counseling_plan"],
                timestamp=result["timestamp"],
                used_rag=used_rag,
                search_results_count=len(search_results),
                search_results=search_results if len(search_results) > 0 else None,
                response_time=response_time
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"상담 계획 생성 실패: {result.get('error', 'Unknown error')}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("상담 계획 수립 중 예상치 못한 오류")
        raise HTTPException(
            status_code=500, 
            detail=f"상담 계획 수립 처리 실패: {str(e)}"
        )


@router.post("/summarize-conversation/")
async def summarize_conversation(request: SummarizeRequest):
    """대화 내용 요약 생성"""
    try:
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]
        
        result = await gemini_service.generate_summary(conversation_history)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "summary": result["summary"],
                "timestamp": result["timestamp"],
                "conversation_length": len(request.conversation_history),
                "summary_type": request.summary_type,
                "includes_action_items": request.include_action_items
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    
    except Exception as e:
        logger.exception("대화 요약 실패")
        raise HTTPException(status_code=500, detail=f"대화 요약 실패: {str(e)}")


@router.post("/extract-keywords/")
async def extract_keywords(request: ExtractKeywordsRequest):
    """텍스트에서 고민 태그/키워드 추출"""
    try:
        result = await gemini_service.generate_keywords(request.text)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "keywords": result["keywords"],
                "timestamp": result["timestamp"],
                "text_length": len(request.text),
                "include_priority": request.include_priority,
                "include_emotions": request.extract_emotions
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    
    except Exception as e:
        logger.exception("키워드 추출 실패")
        raise HTTPException(status_code=500, detail=f"키워드 추출 실패: {str(e)}")

@router.get("/service-status/")
async def get_service_status():
    """서비스 상태 확인"""
    try:
        # Gemini API 상태 확인
        test_result = await gemini_service.generate_counseling_response(
            user_query="안녕하세요. 시스템 상태 확인 테스트입니다.",
            search_results=None
        )
        
        gemini_status = "healthy" if test_result["status"] == "success" else "error"
        
        # Milvus 상태 체크 안전한 버전
        milvus_status = "healthy"
        milvus_info = {}
        try:
            collection = get_milvus_collection()
            # total_entities may be available as collection.num_entities
            total_records = None
            try:
                total_records = collection.num_entities
            except Exception:
                try:
                    total_records = collection.num_entities()  # 일부 버전 차이
                except Exception:
                    total_records = None

            # load state 확인
            is_loaded = False
            try:
                load_state = utility.load_state(collection.name)
                if hasattr(load_state, "name"):
                    is_loaded = load_state.name.lower() == "loaded"
                else:
                    is_loaded = "loaded" in str(load_state).lower()
            except Exception:
                is_loaded = False

            # index 존재 여부 안전 확인
            has_index = False
            try:
                has_index = collection.has_index()
            except Exception:
                # 일부 버전은 collection.indexes 또는 utility API 사용
                try:
                    has_index = len(collection.indexes) > 0
                except Exception:
                    has_index = False

            milvus_info = {
                "total_records": total_records,
                "collection_name": getattr(collection, "name", None),
                "is_loaded": is_loaded,
                "has_index": has_index
            }
        except Exception as e:
            milvus_status = "error"
            milvus_info = {"error": str(e)}

        
        overall_status = "healthy" if gemini_status == "healthy" and milvus_status == "healthy" else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "gemini_api": {
                    "status": gemini_status,
                    "model": "gemini-2.5-flash-lite",
                    "features": ["chat", "summarization", "keyword_extraction", "planning"]
                },
                "milvus_db": {
                    "status": milvus_status,
                    **milvus_info
                },
                "rag_system": {
                    "status": "healthy" if overall_status == "healthy" else "degraded",
                    "search_enabled": milvus_status == "healthy"
                }
            },
            "performance": {
                "average_response_time": "< 3초",
                "rag_search_time": "< 1초",
                "concurrent_users": "최대 10명"
            }
        }
    
    except Exception as e:
        logger.exception("서비스 상태 확인 실패")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/usage-statistics/")
async def get_usage_statistics():
    """서비스 사용 통계 (데모용)"""
    # 실제 구현에서는 데이터베이스에서 실제 통계를 가져와야 합니다
    return {
        "status": "success",
        "period": "최근 30일",
        "statistics": {
            "total_conversations": 156,
            "total_queries": 423,
            "rag_usage_rate": 0.73,
            "most_common_topics": [
                {"topic": "학습지도", "count": 98},
                {"topic": "교우관계", "count": 87},
                {"topic": "행동문제", "count": 65},
                {"topic": "정서지원", "count": 54},
                {"topic": "학부모상담", "count": 41}
            ],
            "average_response_time": 2.3,
            "user_satisfaction": 4.2,
            "peak_usage_hours": ["09:00-10:00", "14:00-15:00", "16:00-17:00"]
        },
        "trends": {
            "weekly_growth": "+12%",
            "monthly_active_teachers": 28,
            "repeat_usage_rate": 0.68
        },
        "generated_at": datetime.now().isoformat()
    }

@router.get("/debug-rag/")
async def debug_rag_system(test_query: str = "학습부진 상담"):
    """RAG 시스템 디버깅용 엔드포인트"""
    try:
        collection = get_milvus_collection()

        # 1. 컬렉션 기본 정보 (is_loaded 대체)
        try:
            load_state = utility.load_state(collection.name)
            if hasattr(load_state, "name"):
                is_loaded = load_state.name.lower() == "loaded"
            else:
                is_loaded = "loaded" in str(load_state).lower()
        except Exception:
            is_loaded = False

        try:
            has_index = collection.has_index()
        except Exception:
            try:
                has_index = len(collection.indexes) > 0
            except Exception:
                has_index = False

        stats = {
            "collection_name": getattr(collection, "name", None),
            "total_entities": getattr(collection, "num_entities", None),
            "is_loaded": is_loaded,
            "has_index": has_index
        }

        # 2. 샘플 데이터 조회 (expr 빈 문자열은 일부 버전에서 오류날 수 있음 -> None으로 처리)
        try:
            sample_data = collection.query(
                expr=None,
                output_fields=["id", "title", "worry_tags"],
                limit=3
            )
        except TypeError:
            # 일부 버전은 limit 파라미터를 사용하지 않음
            sample_data = collection.query(
                expr=None,
                output_fields=["id", "title", "worry_tags"]
            )

        # 3. 테스트 검색 (개선된 통합 함수 사용)
        test_results = await perform_rag_search_unified(test_query, top_k=3)

        return {
            "status": "success",
            "collection_stats": stats,
            "sample_data": sample_data,
            "test_search": {
                "query": test_query,
                "results_count": len(test_results),
                "results": test_results
            }
        }
    except Exception as e:
        logger.exception("RAG 디버깅 실패")
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }