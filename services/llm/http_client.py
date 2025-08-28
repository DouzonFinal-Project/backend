import httpx
from config.settings import settings

class LLMHttpClient:
    def __init__(self):
        self.base = settings.LLM_API_BASE_URL.rstrip("/")
        self.headers = {"Authorization": f"Bearer {settings.LLM_INTERNAL_TOKEN}"}
        self.timeout = settings.LLM_TIMEOUT

    def post(self, path: str, json: dict):
        url = f"{self.base}{path}"
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(url, json=json, headers=self.headers)
            r.raise_for_status()
            return r.json()

    # 필요 엔드포인트에 맞춰 메서드 노출
    def generate(self, payload: dict):         # 예: /llm/generate
        return self.post("/llm/generate", payload)

    def search_records(self, payload: dict):   # 예: /milvus/search-records/
        # AI 서버가 슬래시 종결을 요구하면 그대로 유지
        return self.post("/milvus/search-records/", payload)

llm_http = LLMHttpClient()
