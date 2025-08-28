from sqlalchemy.orm import Session
from models.events import Event as EventModel
import google.generativeai as genai
from sqlalchemy import func
from config.settings import settings
from datetime import datetime, timedelta
import re

# Gemini API 설정
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)


def handle_event_query(message: str, db: Session):
    """이벤트/일정 조회 및 추가 처리"""
    user_message = message.lower()
    
    # 일정 추가 요청
    if any(keyword in user_message for keyword in ["추가", "등록", "만들어", "생성"]):
        return handle_event_add(message, db)
    
    # 주간 일정 조회 요청
    if "이번 주" in user_message or "이번주" in user_message:
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())  # 월요일
        end = start + timedelta(days=6)                  # 일요일
        return handle_event_weekly(start, end, message, db)
    
    # 월간 일정 조회 요청
    month_match = re.search(r'(\d{1,2})월', message)
    if "이번 달" in user_message or "이번달" in user_message or month_match:
        year = datetime.now().year
        month = datetime.now().month
        if month_match:
            month = int(month_match.group(1))
        return handle_event_monthly(year, month, message, db)

    # 기본: 전체 이벤트 목록 조회
    return handle_event_list(message, db)


def handle_event_add(message: str, db: Session):
    """일정 추가 처리"""
    date_patterns = [
        r'내일',
        r'모레',
        r'오늘',
        r'(\d{1,2})월\s*(\d{1,2})일',
        r'(\d{1,2})일',
        r'다음\s*주',
        r'이번\s*주'
    ]
    
    event_date = None
    for pattern in date_patterns:
        match = re.search(pattern, message)
        if match:
            if pattern == r'내일':
                event_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            elif pattern == r'모레':
                event_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
            elif pattern == r'오늘':
                event_date = datetime.now().strftime('%Y-%m-%d')
            elif pattern == r'(\d{1,2})월\s*(\d{1,2})일':
                month, day = match.groups()
                current_year = datetime.now().year
                event_date = f"{current_year}-{int(month):02d}-{int(day):02d}"
            elif pattern == r'(\d{1,2})일':
                day = match.group(1)
                current_month = datetime.now().month
                current_year = datetime.now().year
                event_date = f"{current_year}-{current_month:02d}-{int(day):02d}"
            break
    
    event_title = extract_event_title(message)
    
    if not event_date:
        return "언제 일정을 추가하시겠어요? (예: 내일, 모레, 12월 25일)"
    if not event_title:
        return "어떤 일정을 추가하시겠어요? (예: 축구대회, 수학시험)"
    
    event_type = classify_event_type(event_title)
    
    new_event = EventModel(
        event_name=event_title,
        event_type=event_type,
        date=event_date,
        description=f"{event_title} 일정이 추가되었습니다."
    )
    
    try:
        db.add(new_event)
        db.commit()
        return f"✅ '{event_title}' 일정이 {event_date}에 성공적으로 추가되었습니다!"
    except Exception as e:
        db.rollback()
        return f"❌ 일정 추가 중 오류가 발생했습니다: {str(e)}"


def handle_event_list(message: str, db: Session):
    """전체 이벤트 목록 조회"""
    events = db.query(EventModel).all()
    return build_ai_response(events, message)


def handle_event_weekly(start, end, message, db: Session):
    """주간 이벤트 조회"""
    events = (
        db.query(EventModel)
        .filter(EventModel.date.between(start, end))
        .all()
    )
    return build_ai_response(events, message)


def handle_event_monthly(year: int, month: int, message: str, db: Session):
    """월간 이벤트 조회"""
    events = (
        db.query(EventModel)
        .filter(func.year(EventModel.date) == year)
        .filter(func.month(EventModel.date) == month)
        .all()
    )
    return build_ai_response(events, message)


def build_ai_response(events, message: str):
    """AI 응답 생성 (공통)"""
    if not events:
        return "해당 기간에 등록된 일정이 없습니다."
    
    event_info = [f"{event.event_name} ({event.date}, {event.description})" for event in events]
    event_list = "\n".join([f"{i+1}. {info}" for i, info in enumerate(event_info)])
    
    prompt = f"""
    다음은 학교에 등록된 이벤트/일정 목록입니다:
    
    {event_list}
    
    사용자가 "{message}"라고 질문했습니다. 
    위 정보를 바탕으로 친근하고 자연스러운 한국어로 답변해주세요.
    """
    
    response = model.generate_content(prompt)
    return response.text


def extract_event_title(message: str) -> str:
    """메시지에서 일정 제목만 추출"""
    clean_message = message
    clean_message = re.sub(r'(내일|모레|오늘|다음\s*주|이번\s*주)', '', clean_message)
    clean_message = re.sub(r'\d{1,2}월\s*\d{1,2}일', '', clean_message)
    clean_message = re.sub(r'\d{1,2}일', '', clean_message)
    clean_message = re.sub(r'(일정\s*추가|등록|만들어|생성).*', '', clean_message)
    clean_message = re.sub(r'[을를이에의]', '', clean_message)
    clean_message = clean_message.strip()
    return clean_message if clean_message and len(clean_message) > 1 else None


def classify_event_type(event_title: str) -> str:
    """이벤트 제목을 분석하여 적절한 타입을 반환"""
    event_title_lower = event_title.lower()
    
    exam_keywords = ['시험', '고사', '평가', '테스트', '중간고사', '기말고사', '수능', '모의고사']
    if any(keyword in event_title_lower for keyword in exam_keywords):
        return "시험/평가"
    
    event_keywords = ['대회', '축제', '행사', '체육', '운동회', '체육대회', '축구', '농구', '야구', '배구', '육상', '수영', '체조', '태권도', '검도', '무술', '댄스', '합창', '연극', '뮤지컬', '전시회', '박람회', '페스티벌', '캠프', '수학여행', '견학', '체험학습']
    if any(keyword in event_title_lower for keyword in event_keywords):
        return "행사/활동"
    
    campaign_keywords = ['캠페인', '홍보', '안전', '환경', '재활용', '절약', '기부', '봉사', '자원봉사', '기부금', '모금']
    if any(keyword in event_title_lower for keyword in campaign_keywords):
        return "캠페인"
    
    meeting_keywords = ['상담', '회의', '미팅', '협의', '토론', '세미나', '워크샵', '연수', '교육', '강연', '강의', '특강', '오리엔테이션', '입학식', '졸업식', '시상식', '수료식']
    if any(keyword in event_title_lower for keyword in meeting_keywords):
        return "상담/회의"
    
    prevention_keywords = ['예방', '안전교육', '성교육', '약물예방', '흡연예방', '음주예방', '교통안전', '재난안전', '응급처치', '심폐소생술', '소방훈련', '지진대피훈련']
    if any(keyword in event_title_lower for keyword in prevention_keywords):
        return "예방교육"
    
    work_keywords = ['업무', '교무', '학년', '부서', '팀', '위원회', '운영위원회', '학부모', 'PTA', '동창회', '동문회']
    if any(keyword in event_title_lower for keyword in work_keywords):
        return "업무회의"
    
    return "행사/활동"
