from sqlalchemy.orm import Session
from models.notices import Notice as NoticeModel
from datetime import datetime, timedelta
import google.generativeai as genai
from config.settings import settings

# ✅ Gemini API 설정
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)


def handle_notice_query(message: str, db: Session):
    """
    공지사항 관련 질의 처리
    - "중요 공지 알려줘"
    - "최근 공지 뭐 있어?"
    - "지난주 공지 정리해줘"
    """
    user_message = message.lower()

    # 중요 공지
    if "중요" in user_message:
        return important_notices(db, message)

    # 최근 공지
    if "최근" in user_message or "최신" in user_message or "요즘" in user_message:
        return recent_notices(db, message)

    # 지난주/이번주 공지
    if "이번주" in user_message or "지난주" in user_message:
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday() + (7 if "지난주" in user_message else 0))
        end = start + timedelta(days=6)
        return weekly_notices(db, start, end, message)

    # 기본: 전체 공지 반환
    return all_notices(db, message)


def important_notices(db: Session, message: str):
    notices = db.query(NoticeModel).filter(NoticeModel.is_important == True).all()
    return build_ai_response(notices, message)


def recent_notices(db: Session, message: str, days: int = 7):
    since = datetime.now() - timedelta(days=days)
    notices = db.query(NoticeModel).filter(NoticeModel.created_at >= since).all()
    return build_ai_response(notices, message)


def weekly_notices(db: Session, start, end, message: str):
    notices = (
        db.query(NoticeModel)
        .filter(NoticeModel.created_at.between(start, end))
        .all()
    )
    return build_ai_response(notices, message)


def all_notices(db: Session, message: str):
    notices = db.query(NoticeModel).all()
    return build_ai_response(notices, message)


def build_ai_response(notices, message: str):
    if not notices:
        return "해당 조건에 맞는 공지사항이 없습니다."

    notice_info = [
        f"- {n.title} ({n.created_at.strftime('%Y-%m-%d')}) : {n.content}" for n in notices
    ]
    notice_list = "\n".join(notice_info)

    prompt = f"""
    다음은 공지사항 목록입니다:

    {notice_list}

    사용자가 "{message}" 라고 요청했습니다.
    위 공지사항을 바탕으로 친근하고 자연스러운 한국어로 답변을 생성해 주세요.
    """
    response = model.generate_content(prompt)
    return response.text
