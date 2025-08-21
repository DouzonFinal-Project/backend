from sqlalchemy.orm import Session
import google.generativeai as genai
from config.settings import settings
from models.meetings import Meeting as MeetingModel

# ✅ Gemini API 설정
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)


def handle_meeting_query(message: str, db: Session):
    """
    회의록 관련 질의 처리
    - 요약 요청: "회의 요약해줘", "지난 회의 간단히 정리"
    - 액션 아이템 요청: "회의에서 나온 할 일 알려줘", "해야 할 것 뽑아줘"
    """
    user_message = message.lower()

    # 회의록 조회
    meeting = (
        db.query(MeetingModel)
        .order_by(MeetingModel.created_at.desc())
        .first()
    )
    if not meeting:
        return "❌ 저장된 회의록이 없습니다."

    # 요약 요청
    if "요약" in user_message or "정리" in user_message or "간단히" in user_message:
        return summarize_meeting(meeting.content)

    # 액션 아이템 요청
    if "할 일" in user_message or "해야" in user_message or "액션" in user_message:
        return extract_actions(meeting.content)

    # 기본: 회의록 내용 그대로 반환
    return f"📋 최근 회의록 원문:\n\n{meeting.content}"


def summarize_meeting(content: str) -> str:
    """회의록 요약"""
    prompt = f"""
    다음은 회의록 전문입니다:
    ---
    {content}
    ---
    위 내용을 한국어로 5줄 이내로 간결하게 요약해 주세요.
    """
    response = model.generate_content(prompt)
    return f"📝 회의 요약:\n{response.text}"


def extract_actions(content: str) -> str:
    """회의록 액션 아이템 추출"""
    prompt = f"""
    다음은 회의록 전문입니다:
    ---
    {content}
    ---
    이 회의에서 나온 '실행해야 할 액션 아이템(To-Do)'만 항목별로 추출해서 목록 형태로 정리해 주세요.
    """
    response = model.generate_content(prompt)
    return f"✅ 액션 아이템:\n{response.text}"
