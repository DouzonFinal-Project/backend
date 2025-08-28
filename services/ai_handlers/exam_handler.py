from sqlalchemy.orm import Session
from services.ai_client import ai_client
import json

def generate_exam(payload: dict, db: Session):
    """
    시험지 자동 생성 핸들러
    - 입력: {
        "subject": "국어",
        "unit": "4단원 큰 숲에 담긴 생각과 느낌",
        "level": "중급",
        "question_config": {
            "objective": 10,
            "short_answer": 5,
            "essay": 3
        },
        "types": ["내용이해", "주제파악", "어휘의미"],
        "options": {
            "include_answer": True,
            "include_score": True,
            "student_info": False
        }
      }
    - 출력: {
        "title": "국어 4단원 평가",
        "questions": [
            {
                "id": 1,
                "type": "객관식",
                "question": "다음 글을 읽고 가장 알맞은 것을 고르시오.",
                "options": ["① ...", "② ...", "③ ...", "④ ..."],
                "answer": 2,
                "score": 5
            },
            ...
        ]
      }
    """

    subject = payload.get("subject")
    unit = payload.get("unit")
    level = payload.get("level")
    qcfg = payload.get("question_config", {})
    types = ", ".join(payload.get("types", []))
    opts = payload.get("options", {})

    # ✅ AI 프롬프트 구성
    prompt = f"""
    너는 초등학교 시험지 출제 도우미야.
    아래 조건에 맞는 시험지를 JSON 형식으로 생성해줘.

    - 과목: {subject}
    - 단원: {unit}
    - 난이도: {level}
    - 문제 구성: 객관식 {qcfg.get("objective", 0)}개, 주관식 {qcfg.get("short_answer", 0)}개, 서술형 {qcfg.get("essay", 0)}개
    - 문제 유형: {types}
    - 출력 옵션: 정답 포함({opts.get("include_answer", True)}), 배점 포함({opts.get("include_score", True)})

    출력 형식 (JSON):
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
        # ✅ AI 클라이언트 호출
        response = ai_client.generate(
            prompt=prompt,
            max_tokens=1500
        )

        # ✅ JSON 파싱 시도
        try:
            parsed = json.loads(response)
            return parsed
        except Exception:
            # 혹시 AI 응답이 JSON이 아닐 경우 대비
            return {
                "success": False,
                "raw_response": response,
                "message": "AI 응답을 JSON으로 변환하지 못했습니다"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "시험지 생성 중 오류가 발생했습니다"
        }
