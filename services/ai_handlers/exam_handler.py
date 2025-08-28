from sqlalchemy.orm import Session
from services.ai_client import ai_client
import json

async def generate_exam(payload: dict, db: Session):
    """
    시험지 자동 생성 핸들러 (비동기 버전)
    - 입력: {
        "subject": "국어",
        "unit": "4단원 큰 숲에 담긴 생각과 느낌",
        "level": "중급",
        "question_config": {"objective": 5, "short_answer": 2, "essay": 1},
        "types": ["내용이해", "주제파악"],
        "options": {"include_answer": true, "include_score": true}
      }
    - 출력: {"title": "...", "questions": [...]}
    """

    subject = payload.get("subject")
    unit = payload.get("unit")
    level = payload.get("level")
    qcfg = payload.get("question_config", {})
    types = ", ".join(payload.get("types", []))
    opts = payload.get("options", {})

    # ✅ 프롬프트 구성
    prompt = f"""
    너는 초등학교 시험 문제 출제 도우미야.
    조건에 맞춰 JSON 형식의 시험지를 생성해줘.

    - 과목: {subject}
    - 단원: {unit}
    - 난이도: {level}
    - 문제 구성: 객관식 {qcfg.get("objective", 0)}개, 
                 주관식 {qcfg.get("short_answer", 0)}개, 
                 서술형 {qcfg.get("essay", 0)}개
    - 문제 유형: {types}
    - 옵션: 정답 포함({opts.get("include_answer", True)}), 
             배점 포함({opts.get("include_score", True)})

    출력 예시(JSON):
    {{
      "title": "{subject} {unit} 평가",
      "questions": [
        {{
          "id": 1,
          "type": "객관식",
          "question": "문제 내용",
          "options": ["① 보기1", "② 보기2", "③ 보기3", "④ 보기4"],
          "answer": 2,
          "score": 5
        }}
      ]
    }}
    """

    try:
        # ✅ 비동기 호출 (await 추가)
        response = await ai_client.quick_chat(query=prompt)

        # Gemini 응답 구조 확인 후 JSON 파싱 시도
        ai_text = response.get("message") or response.get("response") or str(response)

        try:
            parsed = json.loads(ai_text)
            return parsed
        except Exception:
            return {
                "success": False,
                "raw_response": ai_text,
                "message": "AI 응답을 JSON으로 변환하지 못했습니다"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "시험지 생성 중 오류가 발생했습니다"
        }
