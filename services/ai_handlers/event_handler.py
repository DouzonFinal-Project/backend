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
    """이벤트/일정 조회 및 추가/삭제 처리"""
    user_message = message.lower()
    
    # 일정 추가 요청 (가장 우선순위)
    if any(keyword in user_message for keyword in ["추가", "등록", "만들어", "생성"]):
        return handle_event_add(message, db)
    
    # 일정 삭제 요청
    if any(keyword in user_message for keyword in ["삭제", "지워", "취소", "제거"]):
        return handle_event_delete(message, db)
    
    # 오늘 일정 조회 요청
    if "오늘" in user_message and any(keyword in user_message for keyword in ["일정", "스케줄", "할일"]):
        today = datetime.now().date()
        return handle_event_daily(today, message, db)
    
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


def handle_event_daily(date, message: str, db: Session):
    """일일 이벤트 조회"""
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    
    events = (
        db.query(EventModel)
        .filter(EventModel.date == date)
        .all()
    )
    
    if not events:
        # 가까운 일정도 함께 조회
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
    
    response = model.generate_content(prompt)
    return response.text


def extract_event_title(message: str) -> str:
    """AI를 사용하여 메시지에서 일정 제목만 추출"""
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
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # 결과가 너무 길거나 의미없는 경우 키워드 기반 추출 사용
        if len(result) > 20 or not result:
            return extract_event_title_by_keywords(message)
        
        return result
        
    except Exception as e:
        print(f"AI 추출 실패, 키워드 기반 추출로 대체: {e}")
        return extract_event_title_by_keywords(message)


def extract_event_title_by_keywords(message: str) -> str:
    """키워드 기반 일정 제목 추출 (AI 실패 시 대체)"""
    # 시간 관련 키워드 제거
    time_keywords = ['오늘', '내일', '모레', '다음주', '이번주', '오후', '오전', '아침', '저녁']
    clean_message = message
    
    for keyword in time_keywords:
        clean_message = clean_message.replace(keyword, '')
    
    # 날짜 패턴 제거
    clean_message = re.sub(r'\d{1,2}월\s*\d{1,2}일', '', clean_message)
    clean_message = re.sub(r'\d{1,2}일', '', clean_message)
    
    # 일정 관련 키워드 제거
    schedule_keywords = ['일정', '추가', '등록', '만들어', '생성', '해줘', '요']
    for keyword in schedule_keywords:
        clean_message = clean_message.replace(keyword, '')
    
    # 조사 제거
    clean_message = re.sub(r'[을를이에의가을로에]', '', clean_message)
    
    # 공백 정리
    clean_message = re.sub(r'\s+', ' ', clean_message).strip()
    
    return clean_message if clean_message and len(clean_message) > 1 else None


def classify_event_type(event_title: str) -> str:
    """AI를 사용하여 일정 유형을 분류"""
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
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # 응답이 유효한 유형인지 확인
        if result in event_types:
            return result
        else:
            # 키워드 기반 분류 (AI 응답이 실패할 경우)
            return classify_event_type_by_keywords(event_title)
            
    except Exception as e:
        print(f"AI 분류 실패, 키워드 기반 분류로 대체: {e}")
        return classify_event_type_by_keywords(event_title)


def classify_event_type_by_keywords(event_title: str) -> str:
    """키워드 기반 일정 유형 분류 (AI 실패 시 대체)"""
    title_lower = event_title.lower()
    
    # 시험/평가
    if any(keyword in title_lower for keyword in ['시험', '평가', '성적', '고사', '테스트']):
        return "시험/평가"
    
    # 행사/활동
    elif any(keyword in title_lower for keyword in ['체육대회', '수학여행', '축제', '운동회', '여행', '대회']):
        return "행사/활동"
    
    # 캠페인
    elif any(keyword in title_lower for keyword in ['캠페인', '안전', '환경', '건강']):
        return "캠페인"
    
    # 예방교육
    elif any(keyword in title_lower for keyword in ['교육', '예방', '안전교육', '약물']):
        return "예방교육"
    
    # 상담/회의
    elif any(keyword in title_lower for keyword in ['면담', '상담', '회의', '미팅', '학부모']):
        return "상담/회의"
    
    # 기본값
    else:
        return "일반"





def handle_event_delete(message: str, db: Session):
    """일정 삭제 처리"""
    # 메시지에서 삭제할 일정 정보 추출
    event_title = extract_event_title_for_delete(message)
    event_date = extract_event_date_for_delete(message)
    
    if not event_title and not event_date:
        return "어떤 일정을 삭제하시겠어요? (예: '체육대회 삭제해줘' 또는 '내일 일정 삭제')"
    
    # 삭제할 일정 찾기
    query = db.query(EventModel)
    
    if event_title:
        query = query.filter(EventModel.event_name.ilike(f"%{event_title}%"))
    
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
    
    # 삭제 실행
    deleted_count = 0
    deleted_events = []
    
    for event in events_to_delete:
        try:
            deleted_events.append(f"{event.event_name} ({event.date})")
            db.delete(event)
            deleted_count += 1
        except Exception as e:
            db.rollback()
            return f"❌ 일정 삭제 중 오류가 발생했습니다: {str(e)}"
    
    try:
        db.commit()
        
        if deleted_count == 1:
            return f"✅ '{deleted_events[0]}' 일정이 성공적으로 삭제되었습니다!"
        else:
            deleted_list = "\n".join([f"- {event}" for event in deleted_events])
            return f"✅ {deleted_count}개의 일정이 삭제되었습니다:\n{deleted_list}"
            
    except Exception as e:
        db.rollback()
        return f"❌ 일정 삭제 중 오류가 발생했습니다: {str(e)}"


def extract_event_title_for_delete(message: str) -> str:
    """삭제 요청에서 일정 제목 추출"""
    # 삭제 관련 키워드 제거
    clean_message = re.sub(r'(삭제|지워|취소|제거).*', '', message)
    clean_message = re.sub(r'일정\s*', '', clean_message)
    
    # 날짜 관련 키워드 제거
    clean_message = re.sub(r'(내일|모레|오늘|다음\s*주|이번\s*주)', '', clean_message)
    clean_message = re.sub(r'\d{1,2}월\s*\d{1,2}일', '', clean_message)
    clean_message = re.sub(r'\d{1,2}일', '', clean_message)
    clean_message = re.sub(r'[을를이에의]', '', clean_message)
    
    clean_message = clean_message.strip()
    return clean_message if clean_message and len(clean_message) > 1 else None


def extract_event_date_for_delete(message: str) -> str:
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
