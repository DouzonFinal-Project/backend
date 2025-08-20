import requests
from datetime import datetime
import sys
import traceback
import json

AI_SERVER_URL = "http://192.168.0.223:8000"  # AI FastAPI 서버 주소

NO_PROXY = {"http": None, "https": None}  # 프록시 무시 설정


def log_request_response(method, url, **kwargs):
    """요청 정보와 응답(또는 에러)을 디버깅용으로 출력"""
    print(f"\n[요청] {method.upper()} {url}")
    if "json" in kwargs:
        print("[요청 JSON]", json.dumps(kwargs["json"], ensure_ascii=False, indent=2))
    try:
        # timeout이 kwargs에 이미 있으면 덮어쓰지 않음
        if "timeout" not in kwargs:
            kwargs["timeout"] = 10

        resp = requests.request(method, url, proxies=NO_PROXY, **kwargs)
        print(f"[응답 코드] {resp.status_code}")
        print(f"[응답 본문] {resp.text[:500]}")  # 길면 500자까지만 출력
        return resp
    except Exception as e:
        print(f"[에러 발생] {e}")
        traceback.print_exc()
        return None


def test_ai_server_connection():
    print("🚀 AI 서버 연결 테스트 시작")
    print(f"AI 서버 주소: {AI_SERVER_URL}")
    print(f"테스트 시간: {datetime.now()}")

    # 환경 정보 출력
    print("\n=== 환경 정보 ===")
    print("Python 실행 파일:", sys.executable)
    print("requests 버전:", requests.__version__)
    print("URL repr:", repr(f"{AI_SERVER_URL}/health"))

    # 1. 헬스체크
    print("\n=== 1. 헬스체크 ===")
    log_request_response("get", f"{AI_SERVER_URL}/health")

    # 2. 상담 기록 추가
    print("\n=== 2. 상담 기록 추가 ===")
    record_data = {
        "title": "연동 테스트",
        "student_query": "백엔드 연동 테스트 중입니다",
        "counselor_answer": "테스트 응답",
        "date": "2025-08-19",
        "student_name": "테스트학생",
        "teacher_name": "백엔드개발자",
        "worry_tags": "연동테스트"
    }
    log_request_response("post", f"{AI_SERVER_URL}/api/milvus/add-record/", json=record_data)

    # 3. 벡터 검색
    print("\n=== 3. 벡터 검색 ===")
    search_data = {"query": "연동 테스트", "top_k": 3}
    log_request_response("post", f"{AI_SERVER_URL}/api/milvus/search-records/", json=search_data)

    # 4. Gemini 채팅
    print("\n=== 4. Gemini 채팅 ===")
    chat_data = {
        "query": "백엔드 연동 테스트가 성공적으로 되었는지 확인해주세요",
        "use_rag": True,
        "search_top_k": 3,
        "student_name": "테스트학생"
    }
    log_request_response("post", f"{AI_SERVER_URL}/api/gemini/counseling-chat/", json=chat_data, timeout=15)

    print("\n=== 테스트 완료 ===")
    return True


if __name__ == "__main__":
    print("🎯 AI 연동 종합 테스트 (디버깅 모드)")
    print("=" * 60)
    test_ai_server_connection()
    print("\n✅ 모든 테스트 완료!")
