import asyncio
import re
import httpx
import json
from typing import List, Dict, Any
from config.settings import settings
from database.db import SessionLocal

class ProblemGeneratorHandler:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.timeout = settings.LLM_TIMEOUT
        self.max_tokens = 8192  # 문제지 생성을 위해 토큰 수 증가
        self.temperature = settings.LLM_TEMPERATURE
    
    async def generate_problem_set(self, settings: Dict[str, Any]) -> str:
        """
        문제출제설정에 맞는 문제지를 생성합니다.
        
        Args:
            settings: 문제 출제 설정 정보
                - subject: 과목
                - units: 선택된 단원들
                - sub_units: 선택된 소단원들 (수학 1단원의 경우)
                - difficulty: 난이도
                - multiple_choice_count: 객관식 문제 수
                - subjective_count: 주관식 문제 수
                - question_types: 선택된 문제 유형들
        
        Returns:
            str: 생성된 문제지 내용
        """
        try:
            # 프롬프트 구성
            prompt = self._build_prompt(settings)
            
            # Gemini API 직접 호출
            system_prompt = "전문적인 교육 문제 출제자입니다."
            response = await self._call_gemini_api(system_prompt, prompt)
            
            # 디버깅: 응답 구조 출력
            print(f"=== Gemini API 응답 구조 ===")
            print(f"Response: {response}")
            print(f"Response type: {type(response)}")
            print(f"Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
            print(f"==========================")
            
            if response and isinstance(response, dict) and not response.get("error"):
                # Gemini 응답에서 텍스트 추출
                try:
                    candidates = response.get("candidates", [])
                    print(f"Candidates: {candidates}")
                    
                    if candidates and len(candidates) > 0:
                        content = candidates[0].get("content", {})
                        print(f"Content: {content}")
                        
                        parts = content.get("parts", [])
                        print(f"Parts: {parts}")
                        
                        if parts and len(parts) > 0:
                            text = parts[0].get("text", "")
                            print(f"Extracted text: {text[:100] if text else 'None'}...")  # 처음 100자만 출력
                            
                            if text and text.strip():
                                # LaTeX 수식을 초등학생이 이해할 수 있는 표기로 변환
                                cleaned_text = self._clean_latex_notation(text)
                                return cleaned_text
                            else:
                                print("추출된 텍스트가 비어있습니다.")
                        else:
                            print("Parts가 비어있습니다.")
                    else:
                        print("Candidates가 비어있습니다.")
                        
                except Exception as parse_error:
                    print(f"응답 파싱 중 오류: {parse_error}")
                    import traceback
                    traceback.print_exc()
                
                # 응답 구조를 다시 확인하고 대체 방법 시도
                print(f"전체 응답을 문자열로 변환 시도...")
                if isinstance(response, dict):
                    # Gemini API 응답의 다른 가능한 구조들 확인
                    if "candidates" in response:
                        candidates = response["candidates"]
                        if candidates and len(candidates) > 0:
                            candidate = candidates[0]
                            if "content" in candidate:
                                content = candidate["content"]
                                if "parts" in content:
                                    parts = content["parts"]
                                    if parts and len(parts) > 0:
                                        part = parts[0]
                                        if "text" in part:
                                            text = part["text"]
                                            if text and text.strip():
                                                cleaned_text = self._clean_latex_notation(text)
                                                return cleaned_text
                    
                    # 직접 텍스트 검색
                    response_str = str(response)
                    if "text" in response_str.lower() or "content" in response_str.lower():
                        print("응답에 text나 content 관련 키가 있습니다.")
                        # JSON 문자열에서 텍스트 추출 시도
                        try:
                            import json
                            response_json = json.dumps(response, ensure_ascii=False)
                            if "text" in response_json:
                                # 간단한 텍스트 추출
                                start_idx = response_json.find('"text": "') + 8
                                if start_idx > 8:
                                    end_idx = response_json.find('"', start_idx)
                                    if end_idx > start_idx:
                                        extracted_text = response_json[start_idx:end_idx]
                                        if extracted_text and len(extracted_text) > 10:  # 의미있는 텍스트인지 확인
                                            cleaned_text = self._clean_latex_notation(extracted_text)
                                            return cleaned_text
                        except Exception as json_error:
                            print(f"JSON 파싱 시도 중 오류: {json_error}")
                    else:
                        print("응답에 text나 content 관련 키가 없습니다.")
                
                return "문제지 생성에 실패했습니다. 다시 시도해주세요."
            elif response and isinstance(response, str):
                # response가 문자열인 경우 (에러 메시지 등)
                return response
            else:
                error_msg = response.get("error", "알 수 없는 오류") if isinstance(response, dict) else str(response)
                return f"문제지 생성에 실패했습니다: {error_msg}"
                
        except Exception as e:
            print(f"문제지 생성 중 오류 발생: {e}")
            return f"문제지 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def generate_problem_set_streaming(self, settings: Dict[str, Any]):
        """
        문제출제설정에 맞는 문제지를 스트리밍으로 생성합니다.
        
        Args:
            settings: 문제 출제 설정 정보
        
        Yields:
            str: 생성된 문제지 내용 (스트리밍)
        """
        try:
            # 프롬프트 구성
            prompt = self._build_prompt(settings)
            
            # Gemini API 스트리밍 호출
            system_prompt = "전문적인 교육 문제 출제자입니다."
            
            # 전체 응답을 버퍼에 모음
            full_response = ""
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent"
                
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": f"{system_prompt}\n\n{prompt}"}]
                        }
                    ],
                    "generationConfig": {
                        "temperature": self.temperature,
                        "maxOutputTokens": self.max_tokens,
                        "topP": 0.8,
                        "topK": 40
                    }
                }
                
                async with client.stream("POST", url, headers=headers, json=payload, params={"key": self.api_key}) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.strip():
                                full_response += line
                        
                        # 완전한 JSON 파싱
                        try:
                            response_data = json.loads(full_response)
                            print(f"=== 파싱된 전체 응답 ===")
                            print(f"Response Data: {response_data}")
                            print(f"==========================")
                            
                            # 각 청크에서 텍스트 추출하여 yield
                            if isinstance(response_data, list):
                                for chunk in response_data:
                                    if "candidates" in chunk and chunk["candidates"]:
                                        candidate = chunk["candidates"][0]
                                        if "content" in candidate and "parts" in candidate["content"]:
                                            parts = candidate["content"]["parts"]
                                            if parts and "text" in parts[0]:
                                                text = parts[0]["text"]
                                                if text and text.strip():
                                                    print(f"=== 추출된 텍스트 청크 ===")
                                                    print(f"Text: {text}")
                                                    print(f"==========================")
                                                    # LaTeX 수식을 초등학생이 이해할 수 있는 표기로 변환
                                                    cleaned_text = self._clean_latex_notation(text)
                                                    yield cleaned_text
                                                    
                        except json.JSONDecodeError as e:
                            print(f"전체 응답 JSON 파싱 오류: {e}")
                            print(f"Raw Response: {full_response}")
                            yield f"응답 파싱 오류: {str(e)}"
                        except Exception as e:
                            print(f"전체 응답 처리 오류: {e}")
                            yield f"응답 처리 오류: {str(e)}"
                    else:
                        error_text = await response.text()
                        yield f"API 오류 (HTTP {response.status_code}): {error_text}"
                        
        except Exception as e:
            print(f"스트리밍 문제지 생성 중 오류 발생: {e}")
            yield f"문제지 생성 중 오류가 발생했습니다: {str(e)}"

    async def _call_gemini_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Gemini API를 직접 호출합니다.
        """
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            
            headers = {
                "Content-Type": "application/json",
            }
            
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": f"{system_prompt}\n\n{user_prompt}"}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": self.temperature,
                    "maxOutputTokens": self.max_tokens,
                    "topP": 0.8,
                    "topK": 40
                }
            }
            
            print(f"=== Gemini API 요청 정보 ===")
            print(f"URL: {url}")
            print(f"Model: {self.model}")
            print(f"Timeout: {self.timeout}")
            print(f"Max Tokens: {self.max_tokens}")
            print(f"Temperature: {self.temperature}")
            print(f"==========================")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    params={"key": self.api_key}
                )
                
                print(f"=== Gemini API 응답 상태 ===")
                print(f"Status Code: {response.status_code}")
                print(f"Response Headers: {dict(response.headers)}")
                print(f"==========================")
                
                if response.status_code == 200:
                    response_data = response.json()
                    print(f"=== Gemini API 응답 데이터 ===")
                    print(f"Response Keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
                    print(f"Response Type: {type(response_data)}")
                    print(f"==========================")
                    return response_data
                elif response.status_code == 503:
                    # 서비스 일시적 사용 불가 - 재시도 로직
                    print("Gemini API 503 에러 발생, 재시도 중...")
                    await asyncio.sleep(2)  # 2초 대기 후 재시도
                    
                    retry_response = await client.post(
                        url,
                        headers=headers,
                        json=payload,
                        params={"key": self.api_key}
                    )
                    
                    if retry_response.status_code == 200:
                        response_data = retry_response.json()
                        print(f"=== 재시도 성공 - Gemini API 응답 데이터 ===")
                        print(f"Response Keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
                        print(f"Response Type: {type(response_data)}")
                        print(f"==========================")
                        return response_data
                    else:
                        return {"error": f"재시도 후에도 실패: HTTP {retry_response.status_code}"}
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
                    
        except httpx.TimeoutException:
            return {"error": "API 요청 시간 초과"}
        except httpx.RequestError as e:
            return {"error": f"API 요청 실패: {str(e)}"}
        except Exception as e:
            return {"error": f"예상치 못한 오류: {str(e)}"}

    async def _call_gemini_streaming_api(self, system_prompt: str, user_prompt: str):
        """
        Gemini API를 스트리밍 방식으로 호출합니다.
        """
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent"
            
            headers = {
                "Content-Type": "application/json",
            }
            
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": f"{system_prompt}\n\n{user_prompt}"}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": self.temperature,
                    "maxOutputTokens": self.max_tokens,
                    "topP": 0.8,
                    "topK": 40
                }
            }
            
            print(f"=== Gemini API 스트리밍 요청 정보 ===")
            print(f"URL: {url}")
            print(f"Model: {self.model}")
            print(f"Timeout: {self.timeout}")
            print(f"Max Tokens: {self.max_tokens}")
            print(f"Temperature: {self.temperature}")
            print(f"==========================")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, headers=headers, json=payload, params={"key": self.api_key}) as response:
                    print(f"=== Gemini API 스트리밍 응답 상태 ===")
                    print(f"Status Code: {response.status_code}")
                    print(f"==========================")
                    
                    if response.status_code == 200:
                        # 전체 응답을 버퍼에 모음
                        full_response = ""
                        async for line in response.aiter_lines():
                            if line.strip():
                                full_response += line
                                print(f"=== 누적된 응답 ===")
                                print(f"Full Response: {full_response}")
                                print(f"==========================")
                        
                        # 완전한 JSON 파싱
                        try:
                            response_data = json.loads(full_response)
                            print(f"=== 파싱된 전체 응답 ===")
                            print(f"Response Data: {response_data}")
                            print(f"==========================")
                            
                            if "candidates" in response_data and response_data["candidates"]:
                                candidate = response_data["candidates"][0]
                                if "content" in candidate and "parts" in candidate["content"]:
                                    parts = candidate["content"]["parts"]
                                    if parts and "text" in parts[0]:
                                        text = parts[0]["text"]
                                        if text and text.strip():
                                            print(f"=== 추출된 텍스트 ===")
                                            print(f"Text: {text}")
                                            print(f"==========================")
                                            yield text
                                            
                        except json.JSONDecodeError as e:
                            print(f"전체 응답 JSON 파싱 오류: {e}")
                            print(f"Raw Response: {full_response}")
                            yield f"응답 파싱 오류: {str(e)}"
                        except Exception as e:
                            print(f"전체 응답 처리 오류: {e}")
                            yield f"응답 처리 오류: {str(e)}"
                    else:
                        error_text = await response.text()
                        yield f"API 오류 (HTTP {response.status_code}): {error_text}"
                        
        except httpx.TimeoutException:
            yield "API 요청 시간 초과"
        except httpx.RequestError as e:
            yield f"API 요청 실패: {str(e)}"
        except Exception as e:
            yield f"예상치 못한 오류: {str(e)}"
    
    def _build_prompt(self, settings: Dict[str, Any]) -> str:
        """
        문제 생성 프롬프트를 구성합니다.
        """
        subject = settings.get('subject', '')
        units = settings.get('units', [])
        sub_units = settings.get('sub_units', [])
        difficulty = settings.get('difficulty', '')
        multiple_choice_count = settings.get('multiple_choice_count', 0)
        subjective_count = settings.get('subjective_count', 0)
        question_types = settings.get('question_types', [])
        
        # 단원 정보 구성
        unit_info = ""
        if units and isinstance(units, list):
            unit_labels = []
            for unit in units:
                if isinstance(unit, dict) and 'label' in unit:
                    unit_labels.append(unit['label'])
                elif isinstance(unit, str):
                    unit_labels.append(unit)
            if unit_labels:
                unit_info = f"선택된 단원: {', '.join(unit_labels)}"
        
        # 소단원 정보 구성 (수학 1단원의 경우)
        sub_unit_info = ""
        if sub_units and isinstance(sub_units, list):
            sub_unit_labels = []
            for sub_unit in sub_units:
                if isinstance(sub_unit, dict) and 'label' in sub_unit:
                    sub_unit_labels.append(sub_unit['label'])
                elif isinstance(sub_unit, str):
                    sub_unit_labels.append(sub_unit)
            if sub_unit_labels:
                sub_unit_info = f"선택된 소단원: {', '.join(sub_unit_labels)}"
        
        # 문제 유형 정보 구성
        question_type_info = ""
        if question_types and isinstance(question_types, list):
            question_type_labels = []
            for qt in question_types:
                if isinstance(qt, dict) and 'label' in qt:
                    question_type_labels.append(qt['label'])
                elif isinstance(qt, str):
                    question_type_labels.append(qt)
            if question_type_labels:
                question_type_info = f"문제 유형: {', '.join(question_type_labels)}"
        
        # 성취수준별 프롬프트 생성
        achievement_prompt = self._get_achievement_level_prompt(subject, difficulty, units)
        
        prompt = f"""
{achievement_prompt}

{subject} 과목 {difficulty} 난이도 문제지를 생성해주세요.

{unit_info}
{sub_unit_info}

객관식 {multiple_choice_count}문제, 주관식 {subjective_count}문제로 구성하고, {question_type_info}를 포함하여 작성해주세요.

## 중요: 성취수준에 맞는 문제 생성
- 아래에 제시된 성취수준을 "참고 기준"으로 사용하여 문제를 생성해주세요
- 성취수준 설명서를 그대로 출력하지 마세요
- 성취수준에 맞는 "구체적인 문제"를 생성해주세요

## 언어 사용 지침:
1. **자연스러운 한국어**: 초등학생이 이해할 수 있는 친근하고 자연스러운 표현 사용
2. **일관된 톤앤매너**: 모든 문제에서 동일한 말투와 어조 유지
3. **적절한 어휘**: {difficulty} 난이도에 맞는 어휘 선택
4. **명확한 문장**: 문장이 길어지지 않도록 간결하고 명확하게 작성
5. **실생활 연계**: 가능한 한 일상생활과 연결된 구체적인 예시 사용

## 문제지 형식:
1. (객관식 문제 내용)
   (1) 보기1
   (2) 보기2
   (3) 보기3
   (4) 보기4

2. (객관식 문제 내용)
   (1) 보기1
   (2) 보기2
   (3) 보기3
   (4) 보기4

3. (주관식 문제 내용)
   답: 

4. (객관식 문제 내용)
   (1) 보기1
   (2) 보기2
   (3) 보기3
   (4) 보기4

5. (주관식 문제 내용)
   답: 

[정답]
1번-(정답번호), 2번-(정답번호), 3번-(답안), 4번-(정답번호), 5번-(답안)

위 설정과 언어 사용 지침에 맞는 자연스럽고 친근한 문제지를 생성해주세요. 

## 주의사항:
- 설정 정보는 문제지 내용에 포함하지 마세요
- "자, 그럼...", "함께 풀어볼까요?" 같은 안내문이나 설명문을 생성하지 마세요
- 문제지만 바로 생성하고, 불필요한 텍스트는 포함하지 마세요
- 문제지 형식에 맞춰 객관식 문제, 주관식 문제, 정답만 깔끔하게 작성해주세요
- **절대 성취수준 설명서를 출력하지 마세요!**

## 소단원별 문제 출제 지침:
{sub_unit_info and f"- 반드시 선택된 소단원({', '.join([sub_unit['label'] if isinstance(sub_unit, dict) else sub_unit for sub_unit in sub_units])})에 맞는 구체적인 문제를 출제해주세요." or ""}
{sub_unit_info and f"- 각 소단원별로 균등하게 문제를 배분해주세요." or ""}
{sub_unit_info and f"- 소단원 내용과 직접적으로 관련된 문제만 출제해주세요." or ""}
{sub_unit_info and f"- 예시: '분수 ÷ 자연수' 소단원이면 분수를 자연수로 나누는 구체적인 문제를 출제해주세요." or ""}

## 문제 배치 방식:
- 객관식과 주관식을 중간중간 섞어서 출제해주세요
- 연속으로 같은 유형의 문제가 나오지 않도록 해주세요
- 예시: 객관식 → 객관식 → 주관식 → 객관식 → 주관식

## 최종 확인사항:
- 성취수준을 "기준"으로 사용하여 문제를 생성했는지 확인
- 성취수준 설명서가 문제지 내용에 포함되지 않았는지 확인
- 실제 문제지만 생성되었는지 확인
"""
        
        return prompt
    
    def _get_achievement_level_prompt(self, subject: str, difficulty: str, units: List[Dict[str, Any]]) -> str:
        """
        과목과 난이도에 따른 성취수준별 프롬프트를 생성합니다.
        """
        if subject == "수학":
            return self._get_math_achievement_prompt(difficulty, units)
        elif subject == "국어":
            return self._get_korean_achievement_prompt(difficulty, units)
        elif subject == "영어":
            return self._get_english_achievement_prompt(difficulty, units)
        elif subject == "사회":
            return self._get_social_achievement_prompt(difficulty, units)
        elif subject == "과학":
            return self._get_science_achievement_prompt(difficulty, units)
        else:
            return f"{subject} 과목의 {difficulty} 난이도에 맞는 문제를 생성해주세요."
    
    def _get_math_achievement_prompt(self, difficulty: str, units: List[Dict[str, Any]]) -> str:
        """
        수학 과목의 성취수준별 프롬프트를 생성합니다.
        """
        # 단원별 영역 확인
        unit_labels = [unit.get('label', '') for unit in units]
        is_number_operation = any('분수의 나눗셈' in label or '소수의 나눗셈' in label for label in unit_labels)
        
        if difficulty == "하":  # A등급 성취수준
            if is_number_operation:
                return """수와 연산 영역의 A등급 성취수준에 맞는 문제를 생성해주세요.

A등급 성취수준 기준:
- 지식·이해: 분수와 소수의 관계를 종합적으로 이해하고, 분수의 사칙계산, 소수의 곱셈과 나눗셈의 계산 원리를 종합적으로 이해하며, 이를 계산 과정에 능숙하게 적용할 수 있다.
- 과정·기능: 분수의 사칙계산, 소수의 곱셈과 나눗셈을 여러 가지 방법으로 계산하고, 그 계산 원리를 설명할 수 있다.
- 가치·태도: 실생활 문제를 해결하는 데 분수의 사칙계산, 소수의 곱셈과 나눗셈이 유용하게 활용됨을 안다.

위 기준에 맞는 고급 수준의 문제를 출제하되, 학생들이 종합적 사고와 비판적 사고를 할 수 있도록 구성해주세요."""
            
            else:
                return """수학 A등급 성취수준에 맞는 문제를 생성해주세요.

A등급 성취수준 기준:
- 지식·이해: 핵심 개념을 종합적으로 이해하고, 다양한 방법으로 문제를 해결할 수 있다.
- 과정·기능: 복잡한 문제를 체계적으로 분석하고, 창의적인 해결 방법을 제시할 수 있다.
- 가치·태도: 수학적 사고의 가치를 인식하고, 적극적으로 문제해결에 참여한다.

위 기준에 맞는 고급 수준의 문제를 출제해주세요."""
        
        elif difficulty == "중":  # B등급 성취수준
            if is_number_operation:
                return """수와 연산 영역의 B등급 성취수준에 맞는 문제를 생성해주세요.

B등급 성취수준 기준:
- 지식·이해: 분수와 소수의 관계를 이해하고, 분수의 사칙계산, 소수의 곱셈과 나눗셈의 계산 원리를 이해하며, 이를 계산 과정에 적용할 수 있다.
- 과정·기능: 분수의 사칙계산, 소수의 곱셈과 나눗셈의 계산 원리에 대한 이해를 바탕으로 그 계산을 할 수 있다.
- 가치·태도: 실생활 문제를 해결하는 데 분수의 사칙계산, 소수의 곱셈과 나눗셈이 활용됨을 안다.

위 기준에 맞는 중급 수준의 문제를 출제하되, 기본 개념 이해와 응용 능력을 확인할 수 있도록 구성해주세요."""
            
            else:
                return """수학 B등급 성취수준에 맞는 문제를 생성해주세요.

B등급 성취수준 기준:
- 지식·이해: 핵심 개념을 이해하고, 기본적인 문제를 해결할 수 있다.
- 과정·기능: 문제를 단계별로 분석하고, 적절한 해결 방법을 선택할 수 있다.
- 가치·태도: 수학적 사고에 관심을 가지고, 문제해결에 참여한다.

위 기준에 맞는 중급 수준의 문제를 출제해주세요."""
        
        else:  # "상" - A등급을 넘어서는 고급 수준
            if is_number_operation:
                return """수와 연산 영역의 A등급을 넘어서는 고급 성취수준에 맞는 문제를 생성해주세요.

고급 성취수준 기준:
- 지식·이해: 분수와 소수의 관계를 심화하여 이해하고, 복잡한 계산 문제를 창의적으로 해결할 수 있다.
- 과정·기능: 다양한 해결 방법을 비교 분석하고, 새로운 문제 상황에 적용할 수 있다.
- 가치·태도: 수학적 사고의 깊이를 인식하고, 창의적 문제해결에 적극적으로 참여한다.

위 기준에 맞는 최고급 수준의 문제를 출제하되, 학생들의 창의적 사고와 고급 수학적 사고를 자극할 수 있도록 구성해주세요."""
            
            else:
                return """수학 A등급을 넘어서는 고급 성취수준에 맞는 문제를 생성해주세요.

고급 성취수준 기준:
- 지식·이해: 핵심 개념을 심화하여 이해하고, 복잡한 문제를 창의적으로 해결할 수 있다.
- 과정·기능: 다양한 해결 방법을 비교 분석하고, 새로운 문제 상황에 적용할 수 있다.
- 가치·태도: 수학적 사고의 깊이를 인식하고, 창의적 문제해결에 적극적으로 참여한다.

위 기준에 맞는 최고급 수준의 문제를 출제해주세요."""
    
    def _get_korean_achievement_prompt(self, difficulty: str, units: List[Dict[str, Any]]) -> str:
        """국어 과목의 성취수준별 프롬프트를 생성합니다."""
        if difficulty == "하":
            return "국어 A등급 성취수준에 맞는 문제를 생성해주세요. 문학 작품을 깊이 있게 이해하고, 비판적 사고를 요구하는 문제를 출제해주세요."
        elif difficulty == "중":
            return "국어 B등급 성취수준에 맞는 문제를 생성해주세요. 기본적인 문학 이해와 응용 능력을 확인할 수 있는 문제를 출제해주세요."
        else:
            return "국어 A등급을 넘어서는 고급 성취수준에 맞는 문제를 생성해주세요. 창의적 사고와 고급 문학적 감상을 요구하는 문제를 출제해주세요."
    
    def _get_english_achievement_prompt(self, difficulty: str, units: List[Dict[str, Any]]) -> str:
        """영어 과목의 성취수준별 프롬프트를 생성합니다."""
        if difficulty == "하":
            return "영어 A등급 성취수준에 맞는 문제를 생성해주세요. 고급 문법과 어휘를 활용한 복잡한 문제를 출제해주세요."
        elif difficulty == "중":
            return "영어 B등급 성취수준에 맞는 문제를 생성해주세요. 기본적인 문법과 어휘를 활용한 문제를 출제해주세요."
        else:
            return "영어 A등급을 넘어서는 고급 성취수준에 맞는 문제를 생성해주세요. 창의적 사고와 고급 영어 능력을 요구하는 문제를 출제해주세요."
    
    def _get_social_achievement_prompt(self, difficulty: str, units: List[Dict[str, Any]]) -> str:
        """사회 과목의 성취수준별 프롬프트를 생성합니다."""
        if difficulty == "하":
            return "사회 A등급 성취수준에 맞는 문제를 생성해주세요. 깊이 있는 분석과 비판적 사고를 요구하는 문제를 출제해주세요."
        elif difficulty == "중":
            return "사회 B등급 성취수준에 맞는 문제를 생성해주세요. 기본적인 개념 이해와 응용 능력을 확인할 수 있는 문제를 출제해주세요."
        else:
            return "사회 A등급을 넘어서는 고급 성취수준에 맞는 문제를 생성해주세요. 창의적 사고와 고급 사회적 분석 능력을 요구하는 문제를 출제해주세요."
    
    def _get_science_achievement_prompt(self, difficulty: str, units: List[Dict[str, Any]]) -> str:
        """과학 과목의 성취수준별 프롬프트를 생성합니다."""
        if difficulty == "하":
            return "과학 A등급 성취수준에 맞는 문제를 생성해주세요. 과학적 원리를 깊이 있게 이해하고, 실험 설계 능력을 요구하는 문제를 출제해주세요."
        elif difficulty == "중":
            return "과학 B등급 성취수준에 맞는 문제를 생성해주세요. 기본적인 과학 개념과 실험 원리를 이해할 수 있는 문제를 출제해주세요."
        else:
            return "과학 A등급을 넘어서는 고급 성취수준에 맞는 문제를 생성해주세요. 창의적 사고와 고급 과학적 탐구 능력을 요구하는 문제를 출제해주세요."

    def _clean_latex_notation(self, text: str) -> str:
        """
        LaTeX 수식 표기를 초등학생이 이해할 수 있는 표기로 변환합니다.
        """
        # 복잡한 분수 표기 변환: $frac{text{분자}}{text{분모}}$ → 분자/분모
        text = re.sub(r'\$frac\{text\{([^}]+)\}\{text\{([^}]+)\}\}\$', r'\1/\2', text)
        
        # 일반 분수 표기 변환: \frac{8}{9} → 8/9
        text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1/\2', text)
        
        # text{} 형태 변환: text{자연수} → 자연수
        text = re.sub(r'text\{([^}]+)\}', r'\1', text)
        
        # 달러 기호 제거: $...$ → ...
        text = re.sub(r'\$([^$]+)\$', r'\1', text)
        
        # 곱하기 기호 변환: \times → ×
        text = re.sub(r'\\times', '×', text)
        
        # 나누기 기호 변환: \div → ÷
        text = re.sub(r'\\div', '÷', text)
        
        # 점 곱하기 기호 변환: \cdot → ·
        text = re.sub(r'\\cdot', '·', text)
        
        # 제곱근 변환: \sqrt{4} → √4
        text = re.sub(r'\\sqrt\{([^}]+)\}', r'√\1', text)
        
        # 제곱 변환: x^2 → x²
        text = re.sub(r'(\w+)\^(\d+)', r'\1²', text)
        
        # 세제곱 변환: x^3 → x³
        text = re.sub(r'(\w+)\^3', r'\1³', text)
        
        # 더하기 기호 변환: \+ → +
        text = re.sub(r'\\\+', '+', text)
        
        # 빼기 기호 변환: \- → -
        text = re.sub(r'\\-', '-', text)
        
        # 등호 기호 변환: \= → =
        text = re.sub(r'\\=', '=', text)
        
        # 괄호 정리: \{ → {, \} → }
        text = re.sub(r'\\\{', '{', text)
        text = re.sub(r'\\\}', '}', text)
        
        # 백슬래시 제거: \ → (제거)
        text = re.sub(r'\\([a-zA-Z])', r'\1', text)
        
        return text

# 싱글톤 인스턴스
problem_generator_handler = ProblemGeneratorHandler()

async def handle_problem_generation(settings: Dict[str, Any]) -> str:
    """
    문제 생성 요청을 처리하는 메인 함수
    """
    return await problem_generator_handler.generate_problem_set(settings) 