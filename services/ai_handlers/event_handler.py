from sqlalchemy.orm import Session
from models.events import Event as EventModel
import google.generativeai as genai
from sqlalchemy import func
from config.settings import settings
from datetime import datetime, timedelta
import re

# ==========================================================
# Gemini API 설정
# ==========================================================
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)


# ==========================================================
# 메인 이벤트 쿼리 분기 처리
# ==========================================================
async def handle_event_query(message: str, db: Session):
    """이벤트/일정 조회 및 추가/삭제 처리"""
    user_message = message.lower()
    
    # 일정 추가 요청
    if any(keyword in user_message for keyword in ["추가", "등록", "만들어", "생성"]):
        return await handle_event_add(message, db)
    
    # 일정 삭제 요청
    if any(keyword in user_message for keyword in ["삭제", "지워", "취소", "제거"]):
        return await handle_event_delete(message, db)
    
    # 오늘 일정 조회
    if "오늘" in user_message and any(keyword in user_message for keyword in ["일정", "스케줄", "할일"]):
        today = datetime.now().date()
        return await handle_event_daily(today, message, db)
    
    # 주간 일정 조회
    if "이번 주" in user_message or "이번주" in user_message:
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())  # 월요일
        end = start + timedelta(days=6)                  # 일요일
        return await handle_event_weekly(start, end, message, db)
    
    # 월간 일정 조회
    month_match = re.search(r'(\d{1,2})월', message)
    if "이번 달" in user_message or "이번달" in user_message or month_match:
        year = datetime.now().year
        month = datetime.now().month
        if month_match:
            month = int(month_match.group(1))
        return await handle_event_monthly(year, month, message, db)

    # 기본: 전체 이벤트 목록
    return await handle_event_list(message, db)


# ==========================================================
# 일정 추가
# ==========================================================
async def handle_event_add(message: str, db: Session):
    """일정 추가 처리
    
    📌 예시 입력:
    - "내일 오후 3시에 수학시험 일정 추가"
    - "모레 체육대회 등록해줘"
    
    📌 예시 출력:
    "✅ '수학시험' 일정이 2025-09-04에 성공적으로 추가되었습니다!"
    """
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
    
    event_title = await extract_event_title(message)
    time_info = await extract_time_info(message)
    
    if not event_date:
        return "언제 일정을 추가하시겠어요? (예: 내일, 모레, 12월 25일)"
    if not event_title:
        return "어떤 일정을 추가하시겠어요? (예: 축구대회, 수학시험)"
    
    event_type = await classify_event_type(event_title)
    
    # Description에 시간 정보 포함
    if time_info:
        description = f"{event_title} {time_info}"
    else:
        description = event_title
    
    new_event = EventModel(
        event_name=event_title,
        event_type=event_type,
        date=event_date,
        description=description
    )
    
    try:
        db.add(new_event)
        db.commit()
        return f"✅ '{event_title}' 일정이 {event_date}에 성공적으로 추가되었습니다!"
    except Exception as e:
        db.rollback()
        return f"❌ 일정 추가 중 오류가 발생했습니다: {str(e)}"


# ==========================================================
# 일정 조회
# ==========================================================
async def handle_event_list(message: str, db: Session):
    """전체 이벤트 목록 조회
    
    📌 예시 입력:
    - "모든 일정 보여줘"
    - "이번 학기 이벤트 알려줘"
    """
    events = db.query(EventModel).all()
    return await build_ai_response(events, message)


async def handle_event_weekly(start, end, message, db: Session):
    """주간 이벤트 조회
    
    📌 예시 입력:
    - "이번주 일정 뭐 있어?"
    """
    events = (
        db.query(EventModel)
        .filter(EventModel.date.between(start, end))
        .all()
    )
    return await build_ai_response(events, message)


async def handle_event_daily(date, message: str, db: Session):
    """일일 이벤트 조회
    
    📌 예시 입력:
    - "오늘 일정 알려줘"
    """
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    events = db.query(EventModel).filter(EventModel.date == date).all()
    
    if not events:
        future_events = (
            db.query(EventModel)
            .filter(EventModel.date > date)
            .order_by(EventModel.date)
            .limit(3)
            .all()
        )
        if future_events:
            future_info = "\n".join([f"- {event.event_name} ({event.date})" for event in future_events])
            return f"현재 날짜({current_date})에 등록된 일정이 없습니다.\n\n다음 일정들도 확인해보세요:\n{future_info}"
        else:
            return f"현재 날짜({current_date})에 등록된 일정이 없습니다."
    
    return await build_ai_response(events, message)


async def handle_event_monthly(year: int, month: int, message: str, db: Session):
    """월간 이벤트 조회
    
    📌 예시 입력:
    - "9월 일정 알려줘"
    - "이번달 스케줄"
    """
    events = (
        db.query(EventModel)
        .filter(func.year(EventModel.date) == year)
        .filter(func.month(EventModel.date) == month)
        .all()
    )
    return await build_ai_response(events, message)


# ==========================================================
# AI 응답 생성
# ==========================================================
async def build_ai_response(events, message: str):
    """AI 응답 생성 (공통)"""
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    
    if not events:
        return f"현재 날짜({current_date})에 등록된 일정이 없습니다."
    
    event_info = [f"{event.event_name} ({event.date}, {event.description})" for event in events]
    event_list = "\n".join([f"{i+1}. {info}" for i, info in enumerate(event_info)])
    
    prompt = f"""
    현재 날짜: {current_date}
    
    다음은 학교에 등록된 이벤트/일정 목록입니다:
    
    {event_list}
    
    사용자가 "{message}"라고 질문했습니다. 
    현재 날짜를 기준으로 위 정보를 바탕으로 친근하고 자연스러운 한국어로 답변해주세요.
    """
    
    response = await model.generate_content_async(prompt)
    return response.text


# ==========================================================
# AI 제목 추출
# ==========================================================
async def extract_event_title(message: str) -> str:
    """AI를 사용하여 메시지에서 일정 제목만 추출
    
    📌 예시:
    - "오늘 오후에 학생면담 일정을 추가해줘" → "학생면담"
    - "내일 수학시험 일정 추가" → "수학시험"
    - "다음주 체육대회 일정 등록" → "체육대회"
    - "오늘 오후에 이예은 상담 일정을 추가해줘" → "이예은 상담"
    """
    prompt = f"""
    다음 메시지에서 일정 제목만 추출해주세요:
    
    메시지: "{message}"
    
    예시:
    - "오늘 오후에 학생면담 일정을 추가해줘" → "학생면담"
    - "내일 수학시험 일정 추가" → "수학시험"
    - "다음주 체육대회 일정 등록" → "체육대회"
    - "오늘 오후에 이예은 상담 일정을 추가해줘" → "이예은 상담"
    
    일정 제목만 정확히 답변해주세요.
    """
    try:
        response = await model.generate_content_async(prompt)
        result = response.text.strip()
        if len(result) > 20 or not result:
            return await extract_event_title_by_keywords(message)
        return result
    except Exception:
        return await extract_event_title_by_keywords(message)


async def extract_time_info(message: str) -> str:
    """메시지에서 시간 정보 추출"""
    time_patterns = [
        r'오후\s*(\d{1,2})시',
        r'오전\s*(\d{1,2})시', 
        r'(\d{1,2})시',
        r'아침',
        r'저녁',
        r'오후',
        r'오전'
    ]
    time_info = []
    used_patterns = set()
    for pattern in time_patterns:
        match = re.search(pattern, message)
        if match and pattern not in used_patterns:
            if pattern == r'오후\s*(\d{1,2})시':
                time_info.append(f"오후 {match.group(1)}시")
                used_patterns.add(r'오후')
            elif pattern == r'오전\s*(\d{1,2})시':
                time_info.append(f"오전 {match.group(1)}시")
                used_patterns.add(r'오전')
            elif pattern == r'(\d{1,2})시':
                if not any('오후' in info or '오전' in info for info in time_info):
                    time_info.append(f"{match.group(1)}시")
            else:
                if not any(info in time_info for info in ['아침', '저녁', '오후', '오전']):
                    time_info.append(match.group(0))
    return " ".join(list(set(time_info))) if time_info else ""


async def extract_event_title_by_keywords(message: str) -> str:
    """키워드 기반 일정 제목 추출 (AI 실패 시 대체)"""
    time_keywords = ['오늘', '내일', '모레', '다음주', '이번주', '오후', '오전', '아침', '저녁']
    clean_message = message
    for keyword in time_keywords:
        clean_message = clean_message.replace(keyword, '')
    clean_message = re.sub(r'\d{1,2}월\s*\d{1,2}일', '', clean_message)
    clean_message = re.sub(r'\d{1,2}일', '', clean_message)
    schedule_keywords = ['일정', '추가', '등록', '만들어', '생성', '해줘', '요']
    for keyword in schedule_keywords:
        clean_message = clean_message.replace(keyword, '')
    clean_message = re.sub(r'[을를이에의가을로에]', '', clean_message)
    clean_message = re.sub(r'\s+', ' ', clean_message).strip()
    return clean_message if clean_message and len(clean_message) > 1 else None


# ==========================================================
# 일정 유형 분류
# ==========================================================
async def classify_event_type(event_title: str) -> str:
    """AI를 사용하여 일정 유형을 분류
    
    📌 분류 유형:
    1. 일반 - 일반적인 학교 일정
    2. 시험/평가 - 시험, 평가, 성적 관련
    3. 행사/활동 - 체육대회, 수학여행, 축제 등
    4. 캠페인 - 안전, 환경, 건강 관련 캠페인
    5. 예방교육 - 안전교육, 약물예방교육 등
    6. 상담/회의 - 면담, 회의, 상담 관련
    
    📌 예시 출력: "상담/회의"
    """
    event_types = ["일반", "시험/평가", "행사/활동", "캠페인", "예방교육", "상담/회의"]
    prompt = f"""
    다음 일정 제목을 보고 6가지 유형 중 하나로 분류해주세요:
    
    일정 제목: {event_title}
    
    분류 유형:
    1. 일반 - 일반적인 학교 일정
    2. 시험/평가 - 시험, 평가, 성적 관련
    3. 행사/활동 - 체육대회, 수학여행, 축제 등
    4. 캠페인 - 안전, 환경, 건강 관련 캠페인
    5. 예방교육 - 안전교육, 약물예방교육 등
    6. 상담/회의 - 면담, 회의, 상담 관련
    
    분류 결과만 정확히 답변해주세요 (예: "상담/회의")
    """
    try:
        response = await model.generate_content_async(prompt)
        result = response.text.strip()
        if result in event_types:
            return result
        else:
            return classify_event_type_by_keywords(event_title)
    except Exception:
        return classify_event_type_by_keywords(event_title)


async def classify_event_type_by_keywords(event_title: str) -> str:
    """키워드 기반 일정 유형 분류 (AI 실패 시 대체)"""
    title_lower = event_title.lower()
    if any(keyword in title_lower for keyword in ['시험', '평가', '성적', '고사', '테스트']):
        return "시험/평가"
    elif any(keyword in title_lower for keyword in ['체육대회', '수학여행', '축제', '운동회', '여행', '대회']):
        return "행사/활동"
    elif any(keyword in title_lower for keyword in ['캠페인', '안전', '환경', '건강']):
        return "캠페인"
    elif any(keyword in title_lower for keyword in ['교육', '예방', '안전교육', '약물']):
        return "예방교육"
    elif any(keyword in title_lower for keyword in ['면담', '상담', '회의', '미팅', '학부모']):
        return "상담/회의"
    else:
        return "일반"


# ==========================================================
# 일정 삭제
# ==========================================================
async def handle_event_delete(message: str, db: Session):
    """일정 삭제 처리
    
    📌 예시 입력:
    - "내일 수학시험 삭제해줘"
    - "체육대회 일정 취소"
    
    📌 예시 출력:
    "✅ '수학시험 (2025-09-04)' 일정이 성공적으로 삭제되었습니다!"
    """
    event_title = await extract_event_title_for_delete(message)
    event_date = await extract_event_date_for_delete(message)
    
    if not event_title and not event_date:
        return "어떤 일정을 삭제하시겠어요? (예: '체육대회 삭제해줘' 또는 '내일 일정 삭제')"
    
    query = db.query(EventModel)
    if event_title:
        title_condition = (
            (EventModel.event_name.ilike(f"%{event_title}%")) |
            (EventModel.description.ilike(f"%{event_title}%"))
        )
        time_info = await extract_time_info(message)
        if time_info:
            time_parts = time_info.split()
            time_conditions = [EventModel.description.ilike(f"%{part}%") for part in time_parts]
            if time_conditions:
                query = query.filter(title_condition | time_conditions[0])
            else:
                query = query.filter(title_condition)
        else:
            query = query.filter(title_condition)
    if event_date:
        query = query.filter(EventModel.date == event_date)
    
    events_to_delete = query.all()
    if not events_to_delete:
        if event_title and event_date:
            return f"'{event_title}' 일정이 {event_date}에 없습니다."
        elif event_title:
            return f"'{event_title}' 일정을 찾을 수 없습니다."
        else:
            return f"{event_date}에 등록된 일정이 없습니다."
    
    deleted_events = []
    try:
        for event in events_to_delete:
            deleted_events.append(f"{event.event_name} ({event.date})")
            db.delete(event)
        db.commit()
        if len(deleted_events) == 1:
            return f"✅ '{deleted_events[0]}' 일정이 성공적으로 삭제되었습니다!"
        else:
            deleted_list = "\n".join([f"- {event}" for event in deleted_events])
            return f"✅ {len(deleted_events)}개의 일정이 삭제되었습니다:\n{deleted_list}"
    except Exception as e:
        db.rollback()
        return f"❌ 일정 삭제 중 오류가 발생했습니다: {str(e)}"


async def extract_event_title_for_delete(message: str) -> str:
    """삭제 요청에서 일정 제목 추출"""
    clean_message = re.sub(r'(삭제|지워|취소|제거).*', '', message)
    clean_message = re.sub(r'일정\s*', '', clean_message)
    clean_message = re.sub(r'(내일|모레|오늘|다음\s*주|이번\s*주)', '', clean_message)
    clean_message = re.sub(r'\d{1,2}월\s*\d{1,2}일', '', clean_message)
    clean_message = re.sub(r'\d{1,2}일', '', clean_message)
    clean_message = re.sub(r'[을를이에의]', '', clean_message)
    return clean_message.strip() if clean_message and len(clean_message) > 1 else None


async def extract_event_date_for_delete(message: str) -> str:
    """삭제 요청에서 날짜 추출"""
    date_patterns = [
        r'내일',
        r'모레',
        r'오늘',
        r'(\d{1,2})월\s*(\d{1,2})일',
        r'(\d{1,2})일'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, message)
        if match:
            if pattern == r'내일':
                return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            elif pattern == r'모레':
                return (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
            elif pattern == r'오늘':
                return datetime.now().strftime('%Y-%m-%d')
            elif pattern == r'(\d{1,2})월\s*(\d{1,2})일':
                month, day = match.groups()
                current_year = datetime.now().year
                return f"{current_year}-{int(month):02d}-{int(day):02d}"
            elif pattern == r'(\d{1,2})일':
                day = match.group(1)
                current_month = datetime.now().month
                current_year = datetime.now().year
                return f"{current_year}-{current_month:02d}-{int(day):02d}"
    return None
