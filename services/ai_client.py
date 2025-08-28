import httpx
from typing import List, Dict, Any, Optional
from config.settings import settings
from pydantic import BaseModel


class AIClientError(Exception):
    """AI 서버 연동 관련 예외"""
    pass


class AIClient:
    """AI 서버(Milvus + Gemini) 통합 클라이언트"""
    
    def __init__(self):
        # AI 서버 베이스 URL (기존 LLM_API_BASE_URL 활용)
        self.base_url = settings.LLM_API_BASE_URL.rstrip("/")
        self.timeout = settings.LLM_TIMEOUT
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """공통 HTTP 요청 처리"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            raise AIClientError("AI 서버 응답 시간 초과")
        except httpx.HTTPStatusError as e:
            raise AIClientError(f"AI 서버 오류 (HTTP {e.response.status_code}): {e.response.text}")
        except Exception as e:
            raise AIClientError(f"AI 서버 연결 실패: {str(e)}")

    # ===============================================================
    # Milvus 벡터 DB 관련 메서드
    # ===============================================================
    
    def add_counseling_record(
        self,
        student_query: str,
        counselor_answer: str,
        date: str,
        title: Optional[str] = None,
        teacher_name: Optional[str] = None,
        student_name: Optional[str] = None,
        worry_tags: Optional[str] = None
    ) -> Dict[str, Any]:
        """상담 기록 추가"""
        payload = {
            "student_query": student_query,
            "counselor_answer": counselor_answer,
            "date": date
        }
        
        # 선택적 필드 추가
        if title:
            payload["title"] = title
        if teacher_name:
            payload["teacher_name"] = teacher_name
        if student_name:
            payload["student_name"] = student_name
        if worry_tags:
            payload["worry_tags"] = worry_tags
            
        return self._make_request("POST", "/api/milvus/add-record/", json=payload)
    
    def bulk_add_counseling_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """일괄 상담 기록 추가"""
        return self._make_request("POST", "/api/milvus/bulk-add-records/", json=records)
    
    def search_counseling_records(
        self,
        query: str,
        top_k: int = 5,
        worry_tag: Optional[str] = None
    ) -> Dict[str, Any]:
        """상담 기록 벡터 검색"""
        payload = {
            "query": query,
            "top_k": top_k
        }
        
        if worry_tag:
            payload["worry_tag"] = worry_tag
            
        return self._make_request("POST", "/api/milvus/search-records/", json=payload)
    
    def update_counseling_record(
        self,
        record_id: int,
        **fields
    ) -> Dict[str, Any]:
        """상담 기록 수정"""
        payload = {"record_id": record_id, **fields}
        return self._make_request("POST", "/api/milvus/update-record/", json=payload)
    
    def delete_counseling_record(self, record_id: int) -> Dict[str, Any]:
        """상담 기록 삭제"""
        payload = {"record_id": record_id}
        return self._make_request("POST", "/api/milvus/delete-record/", json=payload)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계 조회"""
        return self._make_request("GET", "/api/milvus/collection-stats/")

    # ===============================================================
    # Gemini AI 채팅 관련 메서드
    # ===============================================================
    
    def counseling_chat(
        self,
        query: str,
        use_rag: bool = True,
        search_top_k: int = 3,
        worry_tag_filter: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        student_name: Optional[str] = None,
        context_info: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """전문 상담 채팅 (RAG 지원)"""
        payload = {
            "query": query,
            "use_rag": use_rag,
            "search_top_k": search_top_k
        }
        
        # 선택적 필드 추가
        if worry_tag_filter:
            payload["worry_tag_filter"] = worry_tag_filter
        if conversation_history:
            payload["conversation_history"] = conversation_history
        if student_name:
            payload["student_name"] = student_name
        if context_info:
            payload["context_info"] = context_info
            
        return self._make_request("POST", "/api/gemini/counseling-chat/", json=payload)
    
    def quick_chat(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        urgency_level: str = "normal"
    ) -> Dict[str, Any]:
        """간단 채팅 (RAG 없이)"""
        payload = {
            "query": query,
            "urgency_level": urgency_level
        }
        
        if conversation_history:
            payload["conversation_history"] = conversation_history
            
        return self._make_request("POST", "/api/gemini/quick-chat/", json=payload)
    
    def create_counseling_plan(
        self,
        student_name: str,
        grade: int,
        main_concerns: List[str],
        current_situation: str,
        family_background: Optional[str] = None,
        academic_level: Optional[str] = None,
        social_skills: Optional[str] = None
    ) -> Dict[str, Any]:
        """개별 상담 계획 수립"""
        payload = {
            "student_name": student_name,
            "grade": grade,
            "main_concerns": main_concerns,
            "current_situation": current_situation
        }
        
        # 선택적 필드 추가
        if family_background:
            payload["family_background"] = family_background
        if academic_level:
            payload["academic_level"] = academic_level
        if social_skills:
            payload["social_skills"] = social_skills
            
        return self._make_request("POST", "/api/gemini/counseling-plan/", json=payload)
    
    def summarize_conversation(
        self,
        conversation_history: List[Dict[str, str]],
        include_action_items: bool = True,
        summary_type: str = "detailed"
    ) -> Dict[str, Any]:
        """대화 내용 요약"""
        payload = {
            "conversation_history": conversation_history,
            "include_action_items": include_action_items,
            "summary_type": summary_type
        }
        
        return self._make_request("POST", "/api/gemini/summarize-conversation/", json=payload)
    
    def extract_keywords(
        self,
        text: str,
        include_priority: bool = True,
        extract_emotions: bool = False
    ) -> Dict[str, Any]:
        """키워드 추출"""
        payload = {
            "text": text,
            "include_priority": include_priority,
            "extract_emotions": extract_emotions
        }
        
        return self._make_request("POST", "/api/gemini/extract-keywords/", json=payload)
    
    def get_chat_templates(self) -> Dict[str, Any]:
        """상담 템플릿 조회"""
        return self._make_request("GET", "/api/gemini/chat-templates/")
    
    def get_counseling_guidelines(self) -> Dict[str, Any]:
        """상담 가이드라인 조회"""
        return self._make_request("GET", "/api/gemini/counseling-guidelines/")
    
    def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        return self._make_request("GET", "/api/gemini/service-status/")
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """사용 통계 조회"""
        return self._make_request("GET", "/api/gemini/usage-statistics/")





    # ===============================================================
    # 헬스체크
    # ===============================================================
    
    def health_check(self) -> Dict[str, Any]:
        """AI 서버 전체 헬스체크"""
        return self._make_request("GET", "/health")


# 싱글톤 인스턴스
ai_client = AIClient()