from sqlalchemy.orm import Session
from models.events import Event as EventModel
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy import func
from config.settings import settings
from datetime import datetime, timedelta, time
import re

# LangChain Gemini API 설정
model = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7
)


async def handle_event_query(message: str, db: Session):
    """이벤트/일정 조회 및 추가/삭제 처리"""
    user_message = message.lower()
    
    # 일정 추가 요청 (가장 우선순위)
    if any(keyword in user_message for keyword in ["추가", "등록", "만들어", "생성"]):
        return await handle_event_add(message, db)
    
    # 일정 이동/변경 요청
    if any(keyword in user_message for keyword in ["옮겨", "변경", "이동", "바꿔"]):
        return await handle_event_move(message, db)
    
    # 일정 삭제 요청
    if any(keyword in user_message for keyword in ["삭제", "지워", "취소", "제거"]):
        return await handle_event_delete(message, db)
    
    # 오늘 일정 조회 요청
    if "오늘" in user_message and any(keyword in user_message for keyword in ["일정", "스케줄", "할일"]):
        today = datetime.now().date()
        return await handle_event_daily(today, message, db)
    
    # 주간 일정 조회 요청
    if "이번 주" in user_message or "이번주" in user_message:
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())  # 월요일
        end = start + timedelta(days=6)                  # 일요일
        return await handle_event_weekly(start, end, message, db)
    
    # 월간 일정 조회 요청
    month_match = re.search(r'(\d{1,2})월', message)
    if "이번 달" in user_message or "이번달" in user_message or month_match:
        year = datetime.now().year
        month = datetime.now().month
        if month_match:
            month = int(month_match.group(1))
        return await handle_event_monthly(year, month, message, db)

    # 기본: 전체 이벤트 목록 조회
    return await handle_event_list(message, db)


async def handle_event_add(message: str, db: Session):
    """일정 추가 처리"""
    # 여러 이벤트 파싱 시도 (우선순위 1)
    multiple_events = await parse_multiple_events(message)
    if multiple_events:
        return await add_multiple_events(multiple_events, db)
    
    # 기간 파싱 시도 (우선순위 2)
    period_result = await parse_period_dates(message)
    if period_result:
        start_date, end_date = period_result
    else:
        # 단일 날짜 파싱 시도 (우선순위 3)
        single_date = await parse_single_date(message)
        if single_date:
            start_date = end_date = single_date
        else:
            return "언제 일정을 추가하시겠어요? (예: 내일, 모레, 12월 25일, 내일부터 모레까지)"
    
    event_title = await extract_event_title(message)
    time_info = await extract_time_info(message)
    
    if not event_title:
        return "어떤 일정을 추가하시겠어요? (예: 축구대회, 수학시험)"
    
    event_type = await classify_event_type(event_title)
    
    # 시간 파싱
    start_time, end_time = await parse_time_period(message)
    
    # Description 생성 (상세내용이 있으면 사용, 없으면 이벤트명 사용)
    description = await extract_description(message) or event_title
    
    new_event = EventModel(
        event_name=event_title,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        description=description
    )
    
    try:
        db.add(new_event)
        db.commit()
        
        # 시간 정보가 있는 경우 응답에 포함
        if start_time and end_time:
            if start_time == end_time:
                # 단일 시간
                time_str = format_time_for_display(start_time)
                if start_date == end_date:
                    return f"'{event_title}' 일정이 {start_date} {time_str}에 성공적으로 추가되었습니다!"
                else:
                    return f"'{event_title}' 일정이 {start_date}부터 {end_date}까지 {time_str}에 성공적으로 추가되었습니다!"
            else:
                # 시간 기간
                start_time_str = format_time_for_display(start_time)
                end_time_str = format_time_for_display(end_time)
                if start_date == end_date:
                    return f"'{event_title}' 일정이 {start_date} {start_time_str}부터 {end_time_str}까지 성공적으로 추가되었습니다!"
                else:
                    return f"'{event_title}' 일정이 {start_date}부터 {end_date}까지 {start_time_str}부터 {end_time_str}까지 성공적으로 추가되었습니다!"
        else:
            # 시간 정보가 없는 경우 기존 형식
            if start_date == end_date:
                return f"'{event_title}' 일정이 {start_date}에 성공적으로 추가되었습니다!"
            else:
                return f"'{event_title}' 일정이 {start_date}부터 {end_date}까지 성공적으로 추가되었습니다!"
    except Exception as e:
        db.rollback()
        return f"일정 추가 중 오류가 발생했습니다: {str(e)}"


async def handle_event_list(message: str, db: Session):
    """전체 이벤트 목록 조회"""
    events = db.query(EventModel).all()
    return await build_ai_response(events, message)


async def handle_event_weekly(start, end, message, db: Session):
    """주간 이벤트 조회"""
    events = (
        db.query(EventModel)
        .filter(EventModel.start_date.between(start, end))
        .all()
    )
    return await build_ai_response(events, message)


async def handle_event_daily(date, message: str, db: Session):
    """일일 이벤트 조회"""
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    
    events = (
        db.query(EventModel)
        .filter(EventModel.start_date == date)
        .all()
    )
    
    if not events:
        # 가까운 일정도 함께 조회
        future_events = (
            db.query(EventModel)
            .filter(EventModel.start_date > date)
            .order_by(EventModel.start_date)
            .limit(3)
            .all()
        )
        
        if future_events:
            future_info = "\n".join([f"- {event.event_name} ({event.start_date})" for event in future_events])
            return f"현재 날짜({current_date})에 등록된 일정이 없습니다.\n\n다음 일정들도 확인해보세요:\n{future_info}"
        else:
            return f"현재 날짜({current_date})에 등록된 일정이 없습니다."
    
    return await build_ai_response(events, message)


async def handle_event_monthly(year: int, month: int, message: str, db: Session):
    """월간 이벤트 조회"""
    events = (
        db.query(EventModel)
        .filter(func.year(EventModel.start_date) == year)
        .filter(func.month(EventModel.start_date) == month)
        .all()
    )
    return await build_ai_response(events, message)


async def build_ai_response(events, message: str):
    """AI 응답 생성 (공통)"""
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    
    if not events:
        return f"현재 날짜({current_date})에 등록된 일정이 없습니다."
    
    event_info = []
    for event in events:
        # 시간 정보가 있는지 확인
        if event.start_time and event.end_time:
            if event.start_time == event.end_time:
                # 단일 시간
                time_str = format_time_for_display(event.start_time)
                event_info.append(f"{event.event_name} ({event.start_date}, {time_str})")
            else:
                # 시간 범위
                start_time_str = format_time_for_display(event.start_time)
                end_time_str = format_time_for_display(event.end_time)
                event_info.append(f"{event.event_name} ({event.start_date}, {start_time_str}-{end_time_str})")
        else:
            # 시간 정보 없음
            event_info.append(f"{event.event_name} ({event.start_date})")
    
    event_list = "\n".join([f"{i+1}. {info}" for i, info in enumerate(event_info)])
    
    prompt = f"""
    현재 날짜: {current_date}
    
    다음은 학교에 등록된 이벤트/일정 목록입니다:
    
    {event_list}
    
    사용자가 "{message}"라고 질문했습니다. 
    위 정보를 바탕으로 간결하고 전문적인 한국어로 답변해주세요.
    
    답변 형식:
    - 이모지 사용 금지
    - 불필요한 수식어 제거
    - 날짜별로 간단명료하게 정리
    - 시간 정보가 있으면 함께 표시
    - 예시: "9월 9일: 축구대회 (오전9시), 박성주 상담 (오후2시-오후3시)"
    """
    
    response = await model.ainvoke(prompt)
    return response.content


async def extract_event_title(message: str) -> str:
    """AI를 사용하여 메시지에서 일정 제목만 추출"""
    # "상세내용:" 이전 부분만 추출하여 이벤트명 추출
    main_message = message.split('상세내용:')[0].strip()
    
    prompt = f"""
    다음 메시지에서 일정 제목만 추출해주세요:
    
    메시지: "{main_message}"
    
    예시:
    - "10월 25일(토) 오전 10시 축제 일정을 추가해줘" → "축제"
    - "10월 13일(월)부터 10월 17일(금)까지 중간고사 일정을 추가해줘" → "중간고사"
    - "9월 15일(월)부터 9월 19일(금)까지 예방접종 일정을 추가해줘" → "예방접종"
    
    일정 제목만 정확히 답변해주세요. (최대 10자 이내)
    """
    
    try:
        response = await model.ainvoke(prompt)
        result = response.content.strip()
        
        # 결과가 너무 길거나 의미없는 경우 키워드 기반 추출 사용
        if len(result) > 10 or not result:
            return await extract_event_title_by_keywords(main_message)
        
        return result
        
    except Exception as e:
        print(f"AI 추출 실패, 키워드 기반 추출로 대체: {e}")
        return await extract_event_title_by_keywords(main_message)


async def extract_time_info(message: str) -> str:
    """메시지에서 시간 정보 추출"""
    # 더 구체적인 패턴부터 먼저 검색
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
    used_patterns = set()  # 이미 사용된 패턴 추적
    
    for pattern in time_patterns:
        match = re.search(pattern, message)
        if match and pattern not in used_patterns:
            if pattern == r'오후\s*(\d{1,2})시':
                time_info.append(f"오후 {match.group(1)}시")
                used_patterns.add(r'오후')  # 일반 '오후' 패턴 차단
            elif pattern == r'오전\s*(\d{1,2})시':
                time_info.append(f"오전 {match.group(1)}시")
                used_patterns.add(r'오전')  # 일반 '오전' 패턴 차단
            elif pattern == r'(\d{1,2})시':
                # 이미 오후/오전이 있는지 확인
                if not any('오후' in info or '오전' in info for info in time_info):
                    time_info.append(f"{match.group(1)}시")
            else:
                # 아침, 저녁, 오후, 오전은 한 번만 추가
                if not any(info in time_info for info in ['아침', '저녁', '오후', '오전']):
                    time_info.append(match.group(0))
    
    # 중복 제거 및 정리
    time_info = list(set(time_info))
    return " ".join(time_info) if time_info else ""


async def extract_event_title_by_keywords(message: str) -> str:
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


async def classify_event_type(event_title: str) -> str:
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
        response = await model.ainvoke(prompt)
        result = response.content.strip()
        
        # 응답이 유효한 유형인지 확인
        if result in event_types:
            return result
        else:
            # 키워드 기반 분류 (AI 응답이 실패할 경우)
            return classify_event_type_by_keywords(event_title)
            
    except Exception as e:
        print(f"AI 분류 실패, 키워드 기반 분류로 대체: {e}")
        return classify_event_type_by_keywords(event_title)


async def classify_event_type_by_keywords(event_title: str) -> str:
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




async def handle_event_delete(message: str, db: Session):
    """일정 삭제 처리"""
    # 메시지에서 삭제할 일정 정보 추출
    event_title = await extract_event_title_for_delete(message)
    event_date = await extract_event_date_for_delete(message)
    
    if not event_title and not event_date:
        return "어떤 일정을 삭제하시겠어요? (예: '체육대회 삭제해줘' 또는 '내일 일정 삭제')"
    
    # 삭제할 일정 찾기
    query = db.query(EventModel)
    
    if event_title:
        # 제목과 Description에서 모두 검색 (더 유연한 검색)
        title_condition = (
            (EventModel.event_name.ilike(f"%{event_title}%")) |
            (EventModel.description.ilike(f"%{event_title}%"))
        )
        
        # 시간 정보도 별도로 검색
        time_info = await extract_time_info(message)
        if time_info:
            # 시간 정보의 각 부분을 개별적으로 검색
            time_parts = time_info.split()
            time_conditions = []
            for part in time_parts:
                time_conditions.append(EventModel.description.ilike(f"%{part}%"))
            
            # 제목 조건 OR 시간 조건 (더 유연한 검색)
            if time_conditions:
                query = query.filter(
                    title_condition | 
                    (time_conditions[0] if len(time_conditions) == 1 else 
                     time_conditions[0] | time_conditions[1] if len(time_conditions) == 2 else
                     time_conditions[0] | time_conditions[1] | time_conditions[2])
                )
            else:
                query = query.filter(title_condition)
        else:
            query = query.filter(title_condition)
    
    if event_date:
        query = query.filter(EventModel.start_date == event_date)
    
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
            deleted_events.append(f"{event.event_name} ({event.start_date})")
            db.delete(event)
            deleted_count += 1
        except Exception as e:
            db.rollback()
            return f"일정 삭제 중 오류가 발생했습니다: {str(e)}"
    
    try:
        db.commit()
        
        if deleted_count == 1:
            return f"'{deleted_events[0]}' 일정이 성공적으로 삭제되었습니다!"
        else:
            deleted_list = "\n".join([f"- {event}" for event in deleted_events])
            return f"{deleted_count}개의 일정이 삭제되었습니다:\n{deleted_list}"
            
    except Exception as e:
        db.rollback()
        return f"일정 삭제 중 오류가 발생했습니다: {str(e)}"


async def extract_event_title_for_delete(message: str) -> str:
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


async def parse_period_dates(message: str):
    """기간 파싱 (예: "내일부터 모레까지", "9월 10일부터 13일까지")"""
    # 상대적 날짜 기간 패턴
    relative_period_patterns = [
        # "내일부터 모레까지"
        (r'내일부터\s*모레까지', lambda: (
            (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        )),
        # "오늘부터 내일까지"
        (r'오늘부터\s*내일까지', lambda: (
            datetime.now().strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        )),
        # "오늘부터 모레까지"
        (r'오늘부터\s*모레까지', lambda: (
            datetime.now().strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        )),
    ]
    
    # 절대적 날짜 기간 패턴
    absolute_period_patterns = [
        # "9월 10일부터 13일까지"
        (r'(\d{1,2})월\s*(\d{1,2})일부터\s*(\d{1,2})일까지', lambda match: (
            f"{datetime.now().year}-{int(match.group(1)):02d}-{int(match.group(2)):02d}",
            f"{datetime.now().year}-{int(match.group(1)):02d}-{int(match.group(3)):02d}"
        )),
        # "9월 10일부터 10월 5일까지" (괄호 없음)
        (r'(\d{1,2})월\s*(\d{1,2})일부터\s*(\d{1,2})월\s*(\d{1,2})일까지', lambda match: (
            f"{datetime.now().year}-{int(match.group(1)):02d}-{int(match.group(2)):02d}",
            f"{datetime.now().year}-{int(match.group(3)):02d}-{int(match.group(4)):02d}"
        )),
        # "10월 13일(월)부터 10월 17일(금)까지" (괄호 있음)
        (r'(\d{1,2})월\s*(\d{1,2})일\([^)]*\)부터\s*(\d{1,2})월\s*(\d{1,2})일\([^)]*\)까지', lambda match: (
            f"{datetime.now().year}-{int(match.group(1)):02d}-{int(match.group(2)):02d}",
            f"{datetime.now().year}-{int(match.group(3)):02d}-{int(match.group(4)):02d}"
        )),
    ]
    
    # 상대적 날짜 기간 검색
    for pattern, date_func in relative_period_patterns:
        match = re.search(pattern, message)
        if match:
            return date_func()
    
    # 절대적 날짜 기간 검색
    for pattern, date_func in absolute_period_patterns:
        match = re.search(pattern, message)
        if match:
            return date_func(match)
    
    return None


async def parse_single_date(message: str):
    """단일 날짜 파싱 (기존 로직)"""
    date_patterns = [
        r'내일',
        r'모레',
        r'오늘',
        r'(\d{1,2})월\s*(\d{1,2})일',
        r'(\d{1,2})일',
        r'다음\s*주',
        r'이번\s*주'
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


async def parse_multiple_events(message: str):
    """여러 이벤트 파싱 (기간 일정 제외)"""
    
    # 기간 일정 패턴 확인 (같은 제목의 연속 기간)
    period_patterns = [
        r'(\d{1,2}월\s*\d{1,2}일)\s*부터\s*(\d{1,2}월\s*\d{1,2}일)\s*까지\s*([^일정추가]+)',
        r'(\d{1,2}월\s*\d{1,2}일\([^)]*\))\s*부터\s*(\d{1,2}월\s*\d{1,2}일\([^)]*\))\s*까지\s*([^일정추가]+)',
        r'(\d{1,2}일)\s*부터\s*(\d{1,2}일)\s*까지\s*([^일정추가]+)',
        r'내일부터\s*모레까지\s*([^일정추가]+)',
        r'오늘부터\s*(\d{1,2}일)\s*까지\s*([^일정추가]+)'
    ]
    
    # 기간 일정인지 확인
    for pattern in period_patterns:
        if re.search(pattern, message):
            return None  # 기간 일정이면 None 반환 (단일 기간 일정으로 처리)
    
    # AI를 사용하여 여러 이벤트 파싱
    prompt = f"""
    다음 메시지에서 여러 개의 서로 다른 일정이 있는지 확인해주세요:
    
    메시지: "{message}"
    
    각 일정을 다음 형식으로 추출해주세요:
    날짜|이벤트명
    
    예시:
    - "9월 11일에 김민주 상담, 9월 12일엔 박성주 상담 일정을 추가해줘"
    → 9월 11일|김민주 상담
    9월 12일|박성주 상담
    
    - "내일 축구대회, 모레 수학시험 일정 추가"
    → 내일|축구대회
    모레|수학시험
    
    여러 일정이 있으면 각각 한 줄씩 작성해주세요.
    일정이 하나만 있거나 기간 일정이면 빈 문자열을 반환해주세요.
    """
    
    try:
        response = await model.ainvoke(prompt)
        result = response.content.strip()
        
        if not result or "일정이 하나만" in result or "하나의 일정" in result or "기간 일정" in result:
            return None
        
        # 결과 파싱
        events = []
        lines = result.split('\n')
        
        for line in lines:
            line = line.strip()
            if '|' in line:
                date_part, event_part = line.split('|', 1)
                date_part = date_part.strip()
                event_part = event_part.strip()
                
                # 날짜 파싱
                parsed_date = await parse_single_date(f"{date_part} 일정")
                if parsed_date and event_part:
                    events.append({
                        'date': parsed_date,
                        'title': event_part
                    })
        
        return events if len(events) > 1 else None
        
    except Exception as e:
        print(f"AI 여러 이벤트 파싱 실패: {e}")
        return None


async def add_multiple_events(events_data, db: Session):
    """여러 이벤트를 데이터베이스에 추가 (개별 이벤트만)"""
    added_events = []
    failed_events = []
    
    for event_data in events_data:
        try:
            event_title = event_data['title']
            event_date = event_data['date']
            
            # 시간 파싱
            start_time, end_time = await parse_time_period(f"{event_title} {event_date}")
            
            # 이벤트 타입 분류
            event_type = await classify_event_type(event_title)
            
            # Description 생성 (상세내용이 있으면 사용, 없으면 이벤트명 사용)
            description = await extract_description(f"{event_title} {event_date}") or event_title
            
            # 이벤트 생성 (단일 날짜)
            new_event = EventModel(
                event_name=event_title,
                event_type=event_type,
                start_date=event_date,
                end_date=event_date,
                start_time=start_time,
                end_time=end_time,
                description=description
            )
            
            db.add(new_event)
            
            # 시간 정보가 있는 경우 응답에 포함
            if start_time and end_time:
                if start_time == end_time:
                    time_str = format_time_for_display(start_time)
                    added_events.append(f"'{event_title}' 일정이 {event_date} {time_str}에 성공적으로 추가되었습니다!")
                else:
                    start_time_str = format_time_for_display(start_time)
                    end_time_str = format_time_for_display(end_time)
                    added_events.append(f"'{event_title}' 일정이 {event_date} {start_time_str}부터 {end_time_str}까지 성공적으로 추가되었습니다!")
            else:
                added_events.append(f"'{event_title}' 일정이 {event_date}에 성공적으로 추가되었습니다!")
            
        except Exception as e:
            failed_events.append(f"{event_data.get('title', '알 수 없음')}: {str(e)}")
    
    try:
        db.commit()
        
        if failed_events:
            return f"일부 일정 추가에 실패했습니다.\n성공: {', '.join(added_events)}\n실패: {', '.join(failed_events)}"
        else:
            return "\n".join(added_events)
            
    except Exception as e:
        db.rollback()
        return f"일정 추가 중 오류가 발생했습니다: {str(e)}"


async def extract_description(message: str) -> str:
    """메시지에서 상세내용 추출"""
    # "상세내용:" 뒤의 내용을 추출
    detail_match = re.search(r'상세내용:\s*(.+?)(?:\s*$)', message, re.DOTALL)
    if detail_match:
        return detail_match.group(1).strip()
    return None


async def parse_time_period(message: str):
    """시간 기간 파싱 (예: "오전9시부터 오후3시까지", "오전9시")"""
    # 시간 기간 패턴 (시작시간부터 종료시간까지)
    time_period_patterns = [
        # "오전9시부터 오후3시까지"
        (r'오전\s*(\d{1,2})시부터\s*오후\s*(\d{1,2})시까지', lambda match: (
            time(int(match.group(1)), 0),
            time(int(match.group(2)) + 12, 0)
        )),
        # "오후2시부터 오후5시까지"
        (r'오후\s*(\d{1,2})시부터\s*오후\s*(\d{1,2})시까지', lambda match: (
            time(int(match.group(1)) + 12, 0),
            time(int(match.group(2)) + 12, 0)
        )),
        # "오전9시부터 오전11시까지"
        (r'오전\s*(\d{1,2})시부터\s*오전\s*(\d{1,2})시까지', lambda match: (
            time(int(match.group(1)), 0),
            time(int(match.group(2)), 0)
        )),
        # "9시부터 11시까지"
        (r'(\d{1,2})시부터\s*(\d{1,2})시까지', lambda match: (
            time(int(match.group(1)), 0),
            time(int(match.group(2)), 0)
        )),
    ]
    
    # 단일 시간 패턴
    single_time_patterns = [
        # "오전9시"
        (r'오전\s*(\d{1,2})시', lambda match: time(int(match.group(1)), 0)),
        # "오후3시"
        (r'오후\s*(\d{1,2})시', lambda match: time(int(match.group(1)) + 12, 0)),
        # "9시"
        (r'(\d{1,2})시', lambda match: time(int(match.group(1)), 0)),
    ]
    
    # 시간 기간 검색
    for pattern, time_func in time_period_patterns:
        match = re.search(pattern, message)
        if match:
            return time_func(match)
    
    # 단일 시간 검색
    for pattern, time_func in single_time_patterns:
        match = re.search(pattern, message)
        if match:
            single_time = time_func(match)
            return single_time, single_time  # 시작시간과 종료시간이 같음
    
    # 시간 정보가 없으면 None 반환
    return None, None


def format_time_for_display(time_obj):
    """시간 객체를 한국어 표시 형식으로 변환"""
    if not time_obj:
        return ""
    
    hour = time_obj.hour
    minute = time_obj.minute
    
    if hour < 12:
        period = "오전"
        display_hour = hour if hour != 0 else 12
    else:
        period = "오후"
        display_hour = hour - 12 if hour != 12 else 12
    
    if minute == 0:
        return f"{period}{display_hour}시"
    else:
        return f"{period}{display_hour}시{minute}분"


def normalize_text(text):
    """띄어쓰기와 특수문자를 제거하여 텍스트 정규화"""
    if not text:
        return ""
    return re.sub(r'[\s\-_\.]', '', text)


async def parse_event_move_info(message: str):
    """일정 이동 정보 파싱"""
    prompt = f"""
    다음 메시지에서 일정 이동 정보를 추출해주세요:
    "{message}"
    
    추출할 정보:
    1. 기존 날짜 (예: "12일", "9월 10일", "내일")
    2. 일정명 (예: "박성주상담", "수학시험")
    3. 새 날짜 (예: "14일", "9월 15일", "모레")
    
    응답 형식:
    기존날짜: [기존 날짜]
    일정명: [일정명]
    새날짜: [새 날짜]
    
    정보를 찾을 수 없으면 "없음"으로 표시해주세요.
    """
    
    response = await model.ainvoke(prompt)
    content = response.content
    
    # 파싱 결과 추출
    old_date = None
    event_name = None
    new_date = None
    
    for line in content.split('\n'):
        if '기존날짜:' in line:
            old_date = line.split('기존날짜:')[1].strip()
        elif '일정명:' in line:
            event_name = line.split('일정명:')[1].strip()
        elif '새날짜:' in line:
            new_date = line.split('새날짜:')[1].strip()
    
    return old_date, event_name, new_date


async def parse_date_from_text(date_text: str):
    """텍스트에서 날짜 파싱"""
    if not date_text or date_text == "없음":
        return None
    
    current_date = datetime.now()
    
    # 상대적 날짜 처리
    if "내일" in date_text:
        return (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
    elif "모레" in date_text:
        return (current_date + timedelta(days=2)).strftime('%Y-%m-%d')
    elif "어제" in date_text:
        return (current_date - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 숫자만 있는 경우 (예: "12일")
    if re.match(r'^\d+일$', date_text):
        day = int(date_text.replace('일', ''))
        return current_date.replace(day=day).strftime('%Y-%m-%d')
    
    # 월일 형식 (예: "9월 10일")
    month_day_match = re.search(r'(\d+)월\s*(\d+)일', date_text)
    if month_day_match:
        month = int(month_day_match.group(1))
        day = int(month_day_match.group(2))
        return current_date.replace(month=month, day=day).strftime('%Y-%m-%d')
    
    # YYYY-MM-DD 형식
    if re.match(r'\d{4}-\d{2}-\d{2}', date_text):
        return date_text
    
    return None


async def handle_event_move(message: str, db: Session):
    """일정 이동 처리"""
    try:
        # 일정 이동 정보 파싱
        old_date_text, event_name, new_date_text = await parse_event_move_info(message)
        
        if not event_name or event_name == "없음":
            return "어떤 일정을 이동시키시겠어요? (예: 12일 박성주상담을 14일로 옮겨줘)"
        
        if not old_date_text or old_date_text == "없음":
            return "기존 날짜를 알려주세요. (예: 12일 박성주상담을 14일로 옮겨줘)"
        
        if not new_date_text or new_date_text == "없음":
            return "새 날짜를 알려주세요. (예: 12일 박성주상담을 14일로 옮겨줘)"
        
        # 날짜 파싱
        old_date = await parse_date_from_text(old_date_text)
        new_date = await parse_date_from_text(new_date_text)
        
        if not old_date:
            return f"기존 날짜 '{old_date_text}'를 이해할 수 없습니다."
        
        if not new_date:
            return f"새 날짜 '{new_date_text}'를 이해할 수 없습니다."
        
        # 일정 검색 (띄어쓰기 제거 후 비교)
        normalized_event_name = normalize_text(event_name)
        events = db.query(EventModel).filter(
            EventModel.start_date == old_date
        ).all()
        
        target_event = None
        for event in events:
            if normalize_text(event.event_name) == normalized_event_name:
                target_event = event
                break
        
        if not target_event:
            return f"'{event_name}' 일정을 {old_date}에서 찾을 수 없습니다."
        
        # 일정 이동 (날짜 업데이트)
        old_start_date = target_event.start_date
        old_end_date = target_event.end_date
        
        # 기간 일정인 경우 기간 유지
        if old_end_date and old_end_date != old_start_date:
            duration = (old_end_date - old_start_date).days
            new_start_date = datetime.strptime(new_date, '%Y-%m-%d').date()
            new_end_date = new_start_date + timedelta(days=duration)
        else:
            new_start_date = datetime.strptime(new_date, '%Y-%m-%d').date()
            new_end_date = new_start_date
        
        target_event.start_date = new_start_date
        target_event.end_date = new_end_date
        
        db.commit()
        db.refresh(target_event)
        
        # 성공 메시지 생성
        if new_start_date == new_end_date:
            return f"'{event_name}' 일정이 {new_date}로 성공적으로 이동되었습니다!"
        else:
            return f"'{event_name}' 일정이 {new_date}부터 {new_end_date}까지로 성공적으로 이동되었습니다!"
        
    except Exception as e:
        db.rollback()
        return f"일정 이동 중 오류가 발생했습니다: {str(e)}"