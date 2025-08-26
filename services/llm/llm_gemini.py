import os, json, httpx, uuid
import logging

# ✅ 로깅 설정 (콘솔에 DEBUG 레벨 출력)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
TIMEOUT = float(os.getenv("LLM_TIMEOUT", "25"))
DEFAULT_TEMP = float(os.getenv("LLM_TEMPERATURE", "0.2"))
DEFAULT_MAXTOK = int(os.getenv("LLM_MAX_TOKENS", "1024"))


def _client():
    return httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT, connect=10.0))


# ==========================================================
# [공통 호출 함수 with Debug Log]
# ==========================================================
async def _call_gemini(body: dict, params: dict):
    """Gemini API 호출 공통 함수"""
    async with _client() as client:
        try:
            r = await client.post(GEMINI_URL, params=params, json=body)
            r.raise_for_status()
            data = r.json()

            # ✅ 응답 전체 로그 찍기 (디버그용)
            logger.debug("===== GEMINI RAW RESPONSE =====")
            logger.debug(json.dumps(data, ensure_ascii=False, indent=2))
            logger.debug("==============================")

            return data

        except Exception as e:
            logger.error(f"Gemini request failed: {e}")
            return {"error": str(e)}


# ==========================================================
# [JSON 모드]
# ==========================================================
async def generate_json(system_prompt: str, user_prompt: str,
                        temperature: float | None = None, max_tokens: int | None = None):
    t = DEFAULT_TEMP if temperature is None else float(temperature)
    mx = DEFAULT_MAXTOK if max_tokens is None else int(max_tokens)

    prompt = (
        "Return ONLY valid JSON (no markdown, no prose). Use Korean values.\n"
        f"SYSTEM: {system_prompt}\nUSER: {user_prompt}\n"
    )

    params = {"key": GEMINI_KEY}
    body = {
        "generationConfig": {
            "temperature": t,
            "maxOutputTokens": mx,
            "responseMimeType": "application/json"
        },
        "contents": [{"role": "user", "parts": [{"text": prompt}]}]
    }

    data = await _call_gemini(body, params)
    return data  # 일단 원본 그대로 반환 (추후 파싱)


# ==========================================================
# [TEXT 모드]
# ==========================================================
async def generate_text(system_prompt: str, user_prompt: str,
                        temperature: float | None = None, max_tokens: int | None = None):
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

    data = await _call_gemini(body, params)
    return data  # 일단 원본 그대로 반환
