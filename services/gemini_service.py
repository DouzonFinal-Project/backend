# services/gemini_service.py

import os
import asyncio
import logging
from zoneinfo import ZoneInfo
import itertools
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import (
    HumanMessage,   # 사람이 보낸 메세지
    AIMessage,      # AI의 응답 메세지
    SystemMessage,  # 시스템의 지시 메세지
    ToolMessage,    # 도구와 관련된 메세지
    trim_messages   # 메세지 다듬기 함수
    )
from langchain.schema import BaseMessage
from dotenv import load_dotenv

# 환경 설정 로드
load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_CHAT = os.getenv("GEMINI_MODEL_CHAT", "gemini-2.5-flash-lite")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

# 생성자 함수 — 재사용 가능한 LLM 인스턴스 반환
def get_llm(disable_streaming: bool = False) -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=api_key,
        temperature=0.7,
        disable_streaming=disable_streaming
    )
    return llm

# 스트리밍 생성: messages를 받아 async generator로 chunk들을 yield
async def stream_generate(messages: List[BaseMessage]) -> AsyncGenerator[str, None]:
    """
    메시지 리스트(SystemMessage, HumanMessage 등)를 받아
    LLM의 astream()을 통해 부분 결과 문자열을 순차적으로 yield 합니다.
    """
    llm = get_llm(disable_streaming=False)
    generated = ""
    async for chunk in llm.astream(messages):
        # chunk 객체 형식은 라이브러리 버전에 따라 다름 — 안전하게 접근
        content = getattr(chunk, "content", None) or getattr(chunk, "text", None)
        if content:
            generated += content
            yield content
    # 완료 시 아무 것도 반환하지 않음; 호출자는 완성된 텍스트 길이 등 처리 가능

# 비스트리밍 생성: 한 번에 응답 객체 반환 (비동기)
async def generate(messages: List[BaseMessage]) -> dict:
    llm = get_llm(disable_streaming=True)
    resp = await llm.ainvoke(messages)
    content = getattr(resp, "content", "") or getattr(resp, "text", "")
    return {
        "content": content,
        "length": len(content),
        "generated_at": datetime.now().isoformat()
    }
class GeminiChatService:
    """LangChain을 사용한 Gemini 챗봇 서비스"""
    
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL_CHAT,
            google_api_key=GEMINI_API_KEY
        )
        self._chat_semaphore = asyncio.Semaphore(3)  # 동시 요청 제한
        self._max_retries = 3
        self._retry_delay = 1.0
    
    async def _run_blocking(self, fn, *args, **kwargs):
        """비동기로 블로킹 함수 실행"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))
    
    async def _retry_api_call(self, api_func, *args, **kwargs):
        """재시도 로직이 포함된 API 호출"""
        last_error = None
        
        for attempt in range(self._max_retries):
            try:
                return await api_func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    wait_time = self._retry_delay * (2 ** attempt)
                    print(f"API 호출 실패 (시도 {attempt + 1}/{self._max_retries}), {wait_time}초 후 재시도: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"API 호출 최종 실패: {e}")
        
        raise last_error
    
    def _create_system_prompt(self) -> str:
        """초등학교 6학년 담임선생님을 위한 시스템 프롬프트"""
        return """
You are an elementary school counselor assistant.

You are expected to answer the counselor's questions with pedagogical evidence.

You should follow these guidelines:
1. Provide professional yet understandable explanations.
2. Provide specific and actionable advice.
3. Prioritize practical solutions for elementary school students.

Main counseling areas:
1. Peer relationships: Friendships, bullying, conflict resolution, social development.
2. Parent counseling: Home-school connections, parenting styles, communication strategies.
3. Behavioral issues: Rule compliance, distractibility, aggression, and oppositional behavior.

Response structure:

As an elementary school counselor assistant, explain your perspective step-by-step.

Avoid short answers and provide context-sensitive responses.

Please provide all responses in Korean.

At the end of your answer, provide the user with two suggested questions.

Don't introduce yourself and say hello unless the user asks you to.


"""
    
    def _create_context_from_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """검색 결과를 컨텍스트로 변환"""
        if not search_results:
            return "관련 상담 기록이 없습니다."
        
        context_parts = []
        context_parts.append("=== 유사한 과거 상담 기록 ===")
        
        for i, result in enumerate(search_results[:5], 1):  # 최대 5개까지만 사용
            similarity = result.get('similarity', 0)
            title = result.get('title', '제목 없음')
            student_query = result.get('student_query', '')
            counselor_answer = result.get('counselor_answer', '')
            date = result.get('date', '')
            worry_tags = result.get('worry_tags', '')
            teacher_name = result.get('teacher_name', '')
            
            # 유사도가 너무 낮으면 제외
            if similarity < 0.1:
                continue
                
            context_parts.append(f"""
[상담기록 #{i}] (유사도: {similarity:.2f})
- 날짜: {date}
- 담당교사: {teacher_name}
- 제목: {title}
- 고민 태그: {worry_tags}
- 학생 문의: {student_query[:300]}{'...' if len(student_query) > 300 else ''}
- 상담 답변: {counselor_answer[:400]}{'...' if len(counselor_answer) > 400 else ''}
""")
        
        if len(context_parts) == 1:  # 유사한 기록이 없는 경우
            context_parts.append("유사한 상담 기록이 없습니다. 일반적인 교육학적 지식을 바탕으로 답변하겠습니다.")
        
        context_parts.append("=== 상담 기록 종료 ===")
        return "\n".join(context_parts)
    
    async def generate_counseling_response(
        self, 
        user_query: str, 
        search_results: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """개선된 상담 응답 생성"""
        
        async def _generate_response():
            system_prompt = self._create_system_prompt()
            
            # 컨텍스트 생성 - 더 상세한 로깅
            context = ""
            if search_results:
                print(f"RAG 컨텍스트 생성 중... 검색 결과 {len(search_results)}개")
                context = self._create_context_from_search_results(search_results)
                print(f"생성된 컨텍스트 길이: {len(context)} 문자")
            else:
                print("RAG 검색 결과가 없어 기본 모드로 응답 생성")
                context = "관련 상담 기록이 없습니다. 일반적인 교육학적 지식을 바탕으로 답변하겠습니다."
            
            current_time = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
            
            # 프롬프트에 RAG 사용 여부 명시
            rag_indicator = "[RAG 활성화]" if search_results else "[기본 모드]"
            
            full_prompt = f"""{system_prompt}

{rag_indicator}

{context}

[현재 시간: {current_time}]

현재 상담 요청:
{user_query}

위의 {"관련 상담 기록을 참고하여" if search_results else "교육학적 지식을 바탕으로"}, 다음과 같이 답변을 제공해주세요:

전문적이면서도 실무에서 바로 적용할 수 있는 조언을 부탁드립니다.
(응답 길이: 1000자 이내)"""

            # 대화 히스토리 처리
            if conversation_history:
                langchain_history = []
                for msg in conversation_history[-10:]:
                    if msg["role"] == "user":
                        langchain_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        langchain_history.append(AIMessage(content=msg["content"]))
                
                langchain_history.append(HumanMessage(content=full_prompt))
                response = await self.model.ainvoke(langchain_history)
                return response.content
            else:
                response = await self.model.ainvoke([HumanMessage(content=full_prompt)])
                return response.content
        
        try:
            async with self._chat_semaphore:
                response_text = await self._retry_api_call(_generate_response)
                
                # 응답 품질 평가 추가
                response_quality = self._assess_response_quality(response_text, search_results)
                
                return {
                    "status": "success",
                    "response": response_text,
                    "timestamp": datetime.now().isoformat(),
                    "used_context": bool(search_results),
                    "context_count": len(search_results) if search_results else 0,
                    "context_quality": self._assess_context_quality(search_results) if search_results else None,
                    "response_quality": response_quality
                }
                
        except Exception as e:
            print(f"상담 응답 생성 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": f"Gemini API 호출 실패: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def _assess_response_quality(self, response_text: str, search_results: Optional[List]) -> Dict[str, Any]:
        """응답 품질 평가"""
        return {
            "length": len(response_text),
            "has_structure": "**" in response_text or "##" in response_text,
            "used_rag_context": bool(search_results),
            "estimated_sections": response_text.count("**") // 2
        }
    
    def _assess_context_quality(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """검색 결과의 품질을 평가"""
        if not search_results:
            return {"quality": "none", "score": 0}
        
        high_quality_count = sum(1 for r in search_results if r.get('similarity', 0) > 0.8)
        medium_quality_count = sum(1 for r in search_results if 0.6 <= r.get('similarity', 0) <= 0.8)
        
        total_count = len(search_results)
        avg_similarity = sum(r.get('similarity', 0) for r in search_results) / total_count
        
        if avg_similarity > 0.8:
            quality = "excellent"
        elif avg_similarity > 0.6:
            quality = "good"
        elif avg_similarity > 0.4:
            quality = "fair"
        else:
            quality = "poor"
        
        return {
            "quality": quality,
            "average_similarity": round(avg_similarity, 3),
            "high_quality_results": high_quality_count,
            "medium_quality_results": medium_quality_count,
            "total_results": total_count
        }
    
    async def generate_summary(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """대화 내용 요약 생성"""
        async def _generate_summary():
            # 대화 내용을 텍스트로 변환
            conversation_text = "\n".join([
                f"{'👩‍🏫 선생님' if msg['role'] == 'user' else '🤖 AI 상담사'}: {msg['content']}"
                for msg in conversation_history
            ])
            
            summary_prompt = f"""
다음은 초등학교 선생님과 AI 상담사의 대화 내용입니다. 교육 현장에서 활용할 수 있도록 체계적으로 요약해주세요.

대화 내용:
{conversation_text}

다음 형식으로 상담 요약서를 작성해주세요:

## 📋 상담 요약서

### 1. 상담 개요
- 상담 주제: 
- 주요 관심사:
- 상담 시점:

### 2. 문제 상황
- 현재 상황:
- 주요 어려움:
- 관련 요인들:

### 3. 상담 내용 및 제안사항
- 논의된 해결책:
- 구체적 실행 방법:
- 단기/장기 계획:

### 4. 향후 조치사항
- 즉시 실행할 사항:
- 경과 관찰 포인트:
- 추가 지원 필요사항:

### 5. 참고사항
- 주의할 점:
- 학부모 상담 필요성:
- 전문기관 연계 필요성:

실무에서 바로 참고할 수 있도록 간결하고 명확하게 정리해주세요.
"""
            
            response = await self.model.ainvoke(
                [HumanMessage(content=summary_prompt)],
                config={
                    "temperature": 0.3,
                    "max_output_tokens": 2000,
                }
            )

            return response.content
        
        try:
            async with self._chat_semaphore:
                summary_text = await self._retry_api_call(_generate_summary)
                
                return {
                    "status": "success",
                    "summary": summary_text,
                    "timestamp": datetime.now().isoformat(),
                    "conversation_length": len(conversation_history)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"요약 생성 실패: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_keywords(self, text: str) -> Dict[str, Any]:
        """텍스트에서 고민 태그/키워드 추출"""
        async def _generate_keywords():
            keywords_prompt = f"""
다음 상담 내용에서 주요 키워드와 고민 태그를 추출해주세요.

상담 내용:
{text}

초등학교 상담에서 자주 사용되는 표준 카테고리로 분류하여 키워드를 추출하세요:

**학습 관련**: 학습부진, 숙제미완성, 집중력부족, 학습동기저하, 성적하락, 학습습관, 독서부진 등
**교우관계**: 친구관계, 따돌림, 갈등, 사회성부족, 리더십, 소극성, 공격성, 협력 등  
**행동문제**: 규칙위반, 산만함, 충동성, 반항, 거짓말, 도벽, 주의집중 등
**정서문제**: 불안, 우울, 스트레스, 위축, 자신감부족, 완벽주의, 감정조절 등
**가정환경**: 가족갈등, 부모이혼, 경제적어려움, 방임, 과보호, 형제갈등 등
**신체건강**: 식습관, 수면, 위생, 성장, 시력, 비만, 허약체질 등
**기타**: 진로, 특기적성, 창의성, 예체능, 봉사활동, 리더십 등

결과를 다음 형식으로 제시해주세요:
- 주요 카테고리: [카테고리명]
- 핵심 키워드: [키워드1, 키워드2, 키워드3] (최대 5개)
- 상담 우선순위: 높음/중간/낮음
- 전문기관 연계 필요성: 필요/선택적/불필요
"""
            
            response = await self.model.ainvoke(
                [HumanMessage(content=keywords_prompt)],
                config={
                    "temperature": 0.3,
                    "max_output_tokens": 512,
                }
            )

            return response.content
        
        try:
            async with self._chat_semaphore:
                keywords_text = await self._retry_api_call(_generate_keywords)
                
                return {
                    "status": "success",
                    "keywords": keywords_text,
                    "timestamp": datetime.now().isoformat(),
                    "text_length": len(text)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"키워드 추출 실패: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def generate_counseling_plan(
        self, 
        student_info: Dict[str, Any],
        search_results: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        학생 정보와 RAG 검색결과를 기반으로 개별 상담 계획 수립
        
        Args:
            student_info: 학생 기본정보 (이름, 학년, 주요 관심사항 등)
            search_results: RAG 검색으로 찾은 과거 유사 상담 기록들
        """
        async def _generate_plan():
            # 1. 학생 정보 검증 및 기본값 설정
            student_name = student_info.get('student_name', '해당 학생')
            grade = student_info.get('grade', 6)
            main_concerns = student_info.get('main_concerns', [])
            current_situation = student_info.get('current_situation', '')
            query = student_info.get('query', '')
            
            # main_concerns가 문자열로 온 경우 리스트로 변환
            if isinstance(main_concerns, str):
                main_concerns = [concern.strip() for concern in main_concerns.split(',') if concern.strip()]
            
            # 2. RAG 컨텍스트 생성 (기존 _create_context_from_search_results 재사용)
            rag_context = ""
            if search_results and len(search_results) > 0:
                print(f"RAG 기반 상담계획 수립: 검색결과 {len(search_results)}개 활용")
                rag_context = self._create_context_from_search_results(search_results)
                
                # 유사 사례 요약 생성
                similar_cases_summary = self._extract_similar_cases_summary(search_results)
            else:
                print("RAG 검색결과 없음: 일반적인 상담 지식 기반으로 계획 수립")
                rag_context = "관련 과거 상담 기록이 없습니다. 일반적인 교육학적 지식을 바탕으로 계획을 수립합니다."
                similar_cases_summary = ""
            
            # 3. 현재 시간 및 계획 기간 설정
            current_time = datetime.now()
            plan_start_date = current_time.strftime("%Y년 %m월 %d일")
            next_session_date = (current_time + timedelta(days=7)).strftime("%Y-%m-%d")
            
            # 4. 개선된 프롬프트 구성
            plan_prompt = f"""당신은 초등학교 전문 상담교사입니다. 제공된 학생 정보와 과거 유사 상담 사례를 바탕으로 체계적이고 실행 가능한 개별 상담 계획을 수립해주세요.

    === 학생 기본 정보 ===
    • 학생명: {student_name}
    • 학년: {grade}학년
    • 주요 관심사항: {', '.join(main_concerns) if main_concerns else '정보 없음'}
    • 현재 상황: {current_situation if current_situation else query}
    • 계획 수립일: {plan_start_date}

    === 과거 유사 상담 사례 분석 ===
    {rag_context}

    {similar_cases_summary}

    위 정보를 종합하여 다음 형식으로 개별 상담 계획을 작성해주세요:

    ---
    ## 📋 개별 상담 계획서 - {student_name} 학생

    ### 1. 학생 상황 분석
    **• 현재 상황 요약:**
    - 주요 어려움과 관심사항을 구체적으로 기술

    **• 강점 및 자원:**
    - 학생의 긍정적 특성, 관심분야, 지지체계 등

    **• 위험 요인:**
    - 주의 깊게 관찰해야 할 행동이나 상황

    **• 과거 사례 학습:**
    - 유사 사례에서 효과적이었던 접근법 (RAG 기반)

    ### 2. 상담 목표 설정
    **• 단기 목표 (1개월):**
    - 구체적이고 측정 가능한 행동 변화 목표 1-2개

    **• 중기 목표 (1학기):**
    - 단기 목표를 확장한 학습 및 적응 목표

    **• 장기 목표 (1년):**
    - 궁극적인 성장 및 발달 목표

    ### 3. 상담 전략 및 접근법
    **• 기본 접근 방식:**
    - 학생의 특성에 맞는 상담 이론 및 기법

    **• 구체적 기법:**
    - 놀이치료, 인지행동치료, 해결중심치료 등 활용 방안

    **• 동기부여 전략:**
    - 학생의 참여와 지속적 노력을 이끌어낼 방법

    ### 4. 세부 실행 계획
    **• 상담 빈도:** 주 1회, 40분 (총 12회기 계획)

    **• 회기별 활동 계획:**
    1-3회기: 라포 형성 및 문제 탐색
    4-8회기: 핵심 이슈 다루기 및 기법 적용  
    9-12회기: 변화 정착 및 종결 준비

    **• 평가 방법:**
    - 행동 관찰 체크리스트, 자기보고식 척도 등

    ### 5. 지원 체계
    **• 담임교사 협력방안:**
    - 교실 내 지원 전략 및 정기 소통 계획

    **• 학부모 상담 계획:**
    - 가정 연계 방안 및 부모교육 필요성

    **• 전문기관 연계:**
    - 필요시 외부 전문기관 의뢰 기준

    ### 6. 일정 및 점검
    **• 다음 상담일:** {next_session_date}
    **• 중간 평가일:** {(current_time + timedelta(days=30)).strftime("%Y-%m-%d")}
    **• 계획 수정일:** {(current_time + timedelta(days=60)).strftime("%Y-%m-%d")}

    ---
    **※ 주의사항:** 계획 실행 과정에서 학생의 변화와 반응을 지속적으로 관찰하여 필요시 계획을 수정하시기 바랍니다."""

            # 5. Gemini API 호출 (온도 낮춰서 일관된 답변)
            response = await self.model.ainvoke(
                [HumanMessage(content=plan_prompt)],
                config={
                    "temperature": 0.3,  # 계획서는 일관성이 중요하므로 낮은 온도
                    "max_output_tokens": 3000,  # 충분한 토큰 할당
                }
            )

            return response.content
        
        # 6. 에러 처리 및 재시도 로직
        try:
            async with self._chat_semaphore:
                plan_text = await self._retry_api_call(_generate_plan)
                
                # 7. 응답 품질 평가
                plan_quality = self._assess_plan_quality(plan_text, search_results)
                
                return {
                    "status": "success",
                    "counseling_plan": plan_text,
                    "timestamp": datetime.now().isoformat(),
                    "student_name": student_info.get('student_name', ''),
                    "used_rag": bool(search_results),
                    "rag_results_count": len(search_results) if search_results else 0,
                    "plan_quality": plan_quality,
                    "estimated_duration": "12주 (주 1회 상담)",
                    "next_review_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                }
                
        except Exception as e:
            logger.exception(f"상담 계획 수립 실패 - 학생: {student_info.get('student_name', 'Unknown')}")
            return {
                "status": "error",
                "error": f"상담 계획 수립 중 오류 발생: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "student_name": student_info.get('student_name', ''),
                "fallback_available": True  # 기본 템플릿 사용 가능 여부
            }

    def _extract_similar_cases_summary(self, search_results: List[Dict[str, Any]]) -> str:
        """RAG 검색 결과에서 유사 사례의 핵심 정보를 요약"""
        if not search_results:
            return ""
        
        # 높은 유사도의 사례들만 선별
        high_sim_cases = [r for r in search_results if r.get('similarity', 0) > 0.7]
        
        if not high_sim_cases:
            return ""
        
        summary_parts = ["**유사 사례에서 학습한 효과적 접근법:**"]
        
        for i, case in enumerate(high_sim_cases[:3], 1):  # 최대 3개 사례
            worry_tags = case.get('worry_tags', '')
            counselor_answer = case.get('counselor_answer', '')
            
            # 상담사 답변에서 핵심 조언 추출 (첫 200자)
            key_advice = counselor_answer[:200] + "..." if len(counselor_answer) > 200 else counselor_answer
            
            summary_parts.append(f"- 사례 {i} ({worry_tags}): {key_advice}")
        
        return "\n".join(summary_parts)

    def _assess_plan_quality(self, plan_text: str, search_results: Optional[List]) -> Dict[str, Any]:
        """생성된 상담 계획의 품질 평가"""
        return {
            "length": len(plan_text),
            "has_structured_sections": plan_text.count("###") >= 5,  # 최소 5개 섹션
            "includes_timeline": "회기" in plan_text or "주" in plan_text,
            "includes_evaluation": "평가" in plan_text or "점검" in plan_text,
            "rag_integration": bool(search_results) and "사례" in plan_text,
            "actionable_goals": "구체적" in plan_text and "목표" in plan_text,
            "estimated_completeness": min(100, (plan_text.count("###") * 20))  # 섹션 수 기반 완성도
        }

# 전역 서비스 인스턴스
gemini_service = GeminiChatService()