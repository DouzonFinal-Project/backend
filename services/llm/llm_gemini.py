"""
Gemini LLM 호출 서비스 계층
- SDK 없이 httpx로 REST API 호출
- JSON 모드 / 텍스트 모드 두 가지 지원
- .env 설정을 통해 모델, API 키, 파라미터 제어
"""

import os, json, httpx

# 환경 변수 로드
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
TIMEOUT = float(os.getenv("LLM_TIMEOUT", "25"))
DEFAULT_TEMP = float(os.getenv("LLM_TEMPERATURE", "0.2"))
DEFAULT_MAXTOK = int(os.getenv("LLM_MAX_TOKENS", "1024"))

def _client():
    """httpx AsyncClient 기본 생성 (타임아웃 적용)"""
    return httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT, connect=10.0))

async def generate_json(system_prompt: str, user_prompt: str,
                        temperature: float | None = None, max_tokens: int | None = None):
    """
    Gemini를 호출하여 '오직 JSON만' 반환하도록 유도
    - system_prompt: 역할/지시문
    - user_prompt: 사용자 질문/요청
    - temperature, max_tokens: 생성 파라미터 (없으면 기본값 사용)
    """
    t = DEFAULT_TEMP if temperature is None else float(temperature)
    mx = DEFAULT_MAXTOK if max_tokens is None else int(max_tokens)

    # JSON 전용 응답을 위해 프롬프트에 규칙 삽입
    prompt = (
        "Return ONLY valid JSON (no markdown, no prose). Use Korean values.\n"
        f"SYSTEM: {system_prompt}\nUSER: {user_prompt}\n"
    )

    params = {"key": GEMINI_KEY}
    body = {
        "generationConfig": {
            "temperature": t,
            "maxOutputTokens": mx,
            "responseMimeType": "application/json"  # JSON 강제
        },
        "contents": [{"role": "user", "parts": [{"text": prompt}]}]
    }

    # Gemini API 호출
    async with _client() as client:
        r = await client.post(GEMINI_URL, params=params, json=body)
        r.raise_for_status()
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]  # JSON 문자열
        return {"content": json.loads(text), "usage": data.get("usageMetadata", {})}

async def generate_text(system_prompt: str, user_prompt: str,
                        temperature: float | None = None, max_tokens: int | None = None):
    """
    Gemini를 호출하여 일반 텍스트로 응답
    - 주석/서술 포함 가능
    """
    t = DEFAULT_TEMP if temperature is None else float(temperature)
    mx = DEFAULT_MAXTOK if max_tokens is None else int(max_tokens)

    params = {"key": GEMINI_KEY}
    body = {
        "generationConfig": {"temperature": t, "maxOutputTokens": mx},
        "contents": [
            {"role": "user", "parts": [{"text": f"SYSTEM: {system_prompt}"}]},
            {"role": "user", "parts": [{"text": user_prompt}]}
        ]
    }

    # Gemini API 호출
    async with _client() as client:
        r = await client.post(GEMINI_URL, params=params, json=body)
        r.raise_for_status()
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"content": text, "usage": data.get("usageMetadata", {})}
