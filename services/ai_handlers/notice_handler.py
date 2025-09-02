from sqlalchemy.orm import Session
from models.notices import Notice as NoticeModel
import google.generativeai as genai
from sqlalchemy import func
from config.settings import settings
from datetime import datetime, timedelta
import re

# Gemini API 설정
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)


async def handle_notice_query(message: str, db: Session):
    """공지사항 조회 및 관리 처리"""
    user_message = message.lower()
    
    # 이번주 공지사항 조회
    if "이번주" in user_message or "이번 주" in user_message:
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())  # 월요일
        end = start + timedelta(days=6)                  # 일요일
        return await handle_notice_weekly(start, end, message, db)
    
    # 지난주 공지사항 조회
    if "지난주" in user_message or "지난 주" in user_message:
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday() + 7)  # 지난주 월요일
        end = start + timedelta(days=6)                      # 지난주 일요일
        return await handle_notice_weekly(start, end, message, db)
    
    # 오늘 공지사항 조회
    if "오늘" in user_message and any(keyword in user_message for keyword in ["공지", "공지사항"]):
        today = datetime.now().date()
        return await handle_notice_daily(today, message, db)
    
    # 중요 공지사항 조회
    if any(keyword in user_message for keyword in ["중요", "긴급", "필수"]):
        return await handle_important_notices(message, db)
    
    # 전체 공지사항 조회
    if any(keyword in user_message for keyword in ["전체", "모든", "목록"]):
        return await handle_notice_list(message, db)
    
    # 기본: 최근 공지사항 조회
    return await handle_recent_notices(message, db)


async def handle_notice_daily(date, message: str, db: Session):
    """일일 공지사항 조회"""
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    
    notices = (
        db.query(NoticeModel)
        .filter(func.date(NoticeModel.date) == date)
        .order_by(NoticeModel.date.desc())
        .all()
    )
    
    if not notices:
        # 최근 공지사항도 함께 조회
        recent_notices = (
            db.query(NoticeModel)
            .order_by(NoticeModel.date.desc())
            .limit(3)
            .all()
        )
        
        if recent_notices:
            recent_info = "\n".join([f"- {notice.title} ({notice.date})" for notice in recent_notices])
            return f"현재 날짜({current_date})에 등록된 공지사항이 없습니다.\n\n최근 공지사항들도 확인해보세요:\n{recent_info}"
        else:
            return f"현재 날짜({current_date})에 등록된 공지사항이 없습니다."
    
    return await build_notice_response(notices, message)


async def handle_important_notices(message: str, db: Session):
    """중요 공지사항 조회 (기능 제거됨)"""
    return "죄송합니다. 현재 중요 공지사항 구분 기능은 지원하지 않습니다. 전체 공지사항을 조회해드릴까요?"


async def handle_notice_list(message: str, db: Session):
    """전체 공지사항 조회"""
    notices = (
        db.query(NoticeModel)
        .order_by(NoticeModel.date.desc())
        .limit(10)
        .all()
    )
    
    return await build_notice_response(notices, message)


async def handle_notice_weekly(start, end, message: str, db: Session):
    """주간 공지사항 조회"""
    notices = (
        db.query(NoticeModel)
        .filter(NoticeModel.date.between(start, end))
        .order_by(NoticeModel.date.desc())
        .all()
    )
    
    return await build_notice_response_with_summary(notices, message, start, end)


async def handle_recent_notices(message: str, db: Session):
    """최근 공지사항 조회"""
    notices = (
        db.query(NoticeModel)
        .order_by(NoticeModel.date.desc())
        .limit(5)
        .all()
    )
    
    return await build_notice_response(notices, message)


async def build_notice_response(notices, message: str):
    """AI 응답 생성 (공지사항)"""
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    
    if not notices:
        return f"현재 날짜({current_date})에 등록된 공지사항이 없습니다."
    
    notice_info = []
    for notice in notices:
        notice_info.append(f"{notice.title} - {notice.date}")
    
    notice_list = "\n".join([f"{i+1}. {info}" for i, info in enumerate(notice_info)])
    
    prompt = f"""
    현재 날짜: {current_date}
    
    다음은 학교 공지사항 목록입니다:
    
    {notice_list}
    
    사용자가 "{message}"라고 질문했습니다. 
    
    다음 지침에 따라 답변해주세요:
    1. 별표(*) 기호를 사용하지 마세요
    2. 간결하고 전문적인 톤으로 답변하세요
    3. 존댓말을 사용하되 자연스럽게 하세요
    4. 핵심 정보에 집중하고 체계적으로 정리해주세요
    5. 불필요한 반복을 피하고 명확하게 설명해주세요
    6. 이모지나 과도한 친근함 표현을 자제해주세요
    7. 미래 일정은 '예정되어 있습니다' 또는 '있습니다'로 통일해서 표현해주세요
    """
    
    response = await model.generate_content_async(prompt)
    return response.text


async def build_notice_response_with_summary(notices, message: str, start_date, end_date):
    """AI 응답 생성 (공지사항 + 내용 요약)"""
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    period = f"{start_date.strftime('%m월 %d일')} ~ {end_date.strftime('%m월 %d일')}"
    
    if not notices:
        return f"{period} 기간에 등록된 공지사항이 없습니다."
    
    # 날짜별로 공지사항 그룹화
    notices_by_date = {}
    for notice in notices:
        date_str = notice.date.strftime('%m월 %d일')
        if date_str not in notices_by_date:
            notices_by_date[date_str] = []
        notices_by_date[date_str].append(notice)
    
    # 요약 정보 생성
    summary_info = []
    for date_str, date_notices in notices_by_date.items():
        date_summary = f"\n{date_str}:"
        for notice in date_notices:
            # content를 간단히 요약 (최대 50자)
            content_summary = notice.content[:50] + "..." if len(notice.content) > 50 else notice.content
            date_summary += f"\n- {notice.title}: {content_summary}"
        summary_info.append(date_summary)
    
    summary_text = "".join(summary_info)
    
    prompt = f"""
    현재 날짜: {current_date}
    
    다음은 {period} 기간의 공지사항 요약입니다:
    
    {summary_text}
    
    사용자가 "{message}"라고 질문했습니다. 
    
    다음 지침에 따라 답변해주세요:
    1. 별표(*) 기호를 사용하지 마세요
    2. 간결하고 전문적인 톤으로 답변하세요
    3. 존댓말을 사용하되 자연스럽게 하세요
    4. 날짜별로 체계적으로 정리해주세요
    5. 불필요한 반복을 피하고 명확하게 설명해주세요
    6. 이모지나 과도한 친근함 표현을 자제해주세요
    7. 미래 일정은 '예정되어 있습니다' 또는 '있습니다'로 통일해서 표현해주세요
    """
    
    response = await model.generate_content_async(prompt)
    return response.text


