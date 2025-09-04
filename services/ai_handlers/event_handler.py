from sqlalchemy.orm import Session
from models.events import Event as EventModel
import google.generativeai as genai
from sqlalchemy import func
from config.settings import settings
from datetime import datetime, timedelta
import re, json

# ==========================================================
# Gemini API 설정
# ==========================================================
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)


# ==========================================================
# 메인 이벤트 쿼리 (리팩토링)
# ==========================================================
async def handle_event_query(message: str, db: Session):
    """사용자 질의 기반 이벤트 처리 (추가/삭제/조회/복합질의 지원)"""
    user_message = message.lower()

    # ---------------------------
    # 1. 삭제 요청
    # ---------------------------
    if re.search(r"(삭제|지워|없애|취소|제거)", user_message):
        return await handle_event_delete(message, db)

    # ---------------------------
    # 2. 추가 요청
    # ---------------------------
    if re.search(r"(추가|등록|넣어|만들어|생성)", user_message):
        return await handle_event_add(message, db)

    # ---------------------------
    # 3. 특정 기간 조회 (오늘/주간/월간)
    # ---------------------------
    if "오늘" in user_message:
        return await handle_event_daily(datetime.now().date(), message, db)

    if re.search(r"(이번주|다음주|주간)", user_message):
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())  # 이번주 월요일
        end = start + timedelta(days=6)                  # 이번주 일요일
        return await handle_event_weekly(start, end, message, db)

    if re.search(r"(이번달|다음달|\d{1,2}월)", user_message):
        year = datetime.now().year
        month = datetime.now().month
        month_match = re.search(r'(\d{1,2})월', message)
        if month_match:
            month = int(month_match.group(1))
        return await handle_event_monthly(year, month, message, db)

    # ---------------------------
    # 4. 복합 질의: 유형 + 기간
    # 예) "이번주 시험 일정 알려줘"
    # ---------------------------
    event_type = await classify_event_type(user_message)
    if event_type and event_type != "일반":
        today = datetime.now().date()

        # 이번주 + 유형
        if "이번주" in user_message:
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            events = (
                db.query(EventModel)
                .filter(EventModel.date.between(start, end))
                .filter(EventModel.event_type == event_type)
                .all()
            )
            return await build_ai_response(events, message)

        # 이번달 + 유형
        if "이번달" in user_message or "이번 달" in user_message:
            events = (
                db.query(EventModel)
                .filter(func.year(EventModel.date) == today.year)
                .filter(func.month(EventModel.date) == today.month)
                .filter(EventModel.event_type == event_type)
                .all()
            )
            return await build_ai_response(events, message)

    # ---------------------------
    # 5. fallback → AI intent 분석
    # ---------------------------
    prompt = f"""
    사용자가 "{message}" 라고 입력했습니다.
    이 요청을 다음 항목으로 분석해서 JSON으로 답해주세요:
    - action: add / delete / query
    - period: today / week / month / none
    - event_type: 시험/평가, 행사/활동, 상담/회의, 캠페인, 예방교육, 일반 중 하나
    """
    try:
        response = await model.generate_content_async(prompt)
        result = json.loads(response.text)
        action = result.get("action")
        period = result.get("period")
        e_type = result.get("event_type")

        if action == "add":
            return await handle_event_add(message, db)
        elif action == "delete":
            return await handle_event_delete(message, db)
        elif action == "query":
            return await handle_event_ai_query(period, e_type, message, db)
    except Exception:
        pass

    # ---------------------------
    # 6. 기본: 전체 이벤트 목록
    # ---------------------------
    return await handle_event_list(message, db)


# ==========================================================
# 일정 추가 (단일 + 범위 날짜 지원)
# ==========================================================
async def handle_event_add(message: str, db: Session):
    """일정 추가 처리 (단일 날짜 및 범위 날짜 지원)"""

    # 1. 날짜 범위 패턴 체크 (예: "24일부터 26일")
    range_match = re.search(r'(\d{1,2})일부터\s*(\d{1,2})일', message)
    if range_match:
        start_day, end_day = map(int, range_match.groups())
        current_year = datetime.now().year
        current_month = datetime.now().month

        event_title = await extract_event_title(message)
        time_info = await extract_time_info(message)

        if not event_title:
            return "어떤 일정을 추가하시겠어요? (예: 축구대회, 수학시험)"

        event_type = await classify_event_type(event_title)
        added_events = []

        try:
            for day in range(start_day, end_day + 1):
                event_date = f"{current_year}-{current_month:02d}-{day:02d}"
                description = f"{event_title} {time_info}" if time_info else event_title

                new_event = EventModel(
                    event_name=event_title,
                    event_type=event_type,
                    date=event_date,
                    description=description
                )
                db.add(new_event)
                added_events.append(event_date)

            db.commit()
            return f"✅ '{event_title}' 일정이 {added_events[0]} ~ {added_events[-1]} 동안 성공적으로 추가되었습니다!"
        except Exception as e:
            db.rollback()
            return f"❌ 일정 추가 중 오류가 발생했습니다: {str(e)}"

    # 2. 단일 날짜 패턴 처리
    date_patterns = [
        r'내일',
        r'모레',
        r'오늘',
        r'(\d{1,2})월\s*(\d{1,2})일',
        r'(\d{1,2})일',
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
    description = f"{event_title} {time_info}" if time_info else event_title

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
# 일정 조회 핸들러
# ==========================================================
async def handle_event_list(message: str, db: Session):
    events = db.query(EventModel).all()
    return await build_ai_response(events, message)

async def handle_event_weekly(start, end, message, db: Session):
    events = db.query(EventModel).filter(EventModel.date.between(start, end)).all()
    return await build_ai_response(events, message)

async def handle_event_daily(date, message: str, db: Session):
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
# 보조 함수: 일정 제목, 시간, 유형 추출
# ==========================================================
async def extract_event_title(message: str) -> str:
    prompt = f"""
    다음 메시지에서 일정 제목만 추출해주세요:
    메시지: "{message}"
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
    time_patterns = [
        r'오후\s*(\d{1,2})시',
        r'오전\s*(\d{1,2})시', 
        r'(\d{1,2})시',
        r'아침', r'저녁', r'오후', r'오전'
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
                if not any(info in time_info for info in ['아침','저녁','오후','오전']):
                    time_info.append(match.group(0))
    return " ".join(list(set(time_info))) if time_info else ""

async def extract_event_title_by_keywords(message: str) -> str:
    time_keywords = ['오늘','내일','모레','다음주','이번주','오후','오전','아침','저녁']
    clean_message = message
    for keyword in time_keywords:
        clean_message = clean_message.replace(keyword, '')
    clean_message = re.sub(r'\d{1,2}월\s*\d{1,2}일', '', clean_message)
    clean_message = re.sub(r'\d{1,2}일', '', clean_message)
    schedule_keywords = ['일정','추가','등록','만들어','생성','해줘','요']
    for keyword in schedule_keywords:
        clean_message = clean_message.replace(keyword, '')
    clean_message = re.sub(r'[을를이에의가로]', '', clean_message)
    clean_message = re.sub(r'\s+', ' ', clean_message).strip()
    return clean_message if clean_message and len(clean_message) > 1 else None

async def classify_event_type(event_title: str) -> str:
    event_types = ["일반","시험/평가","행사/활동","캠페인","예방교육","상담/회의"]
    prompt = f"""
    다음 일정 제목을 보고 6가지 유형 중 하나로 분류해주세요:
    일정 제목: {event_title}
    분류 유형: {", ".join(event_types)}
    결과만 출력
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
    title_lower = event_title.lower()
    if any(k in title_lower for k in ['시험','평가','성적','고사','테스트']):
        return "시험/평가"
    elif any(k in title_lower for k in ['체육대회','수학여행','축제','운동회','여행','대회']):
        return "행사/활동"
    elif any(k in title_lower for k in ['캠페인','안전','환경','건강']):
        return "캠페인"
    elif any(k in title_lower for k in ['교육','예방','안전교육','약물']):
        return "예방교육"
    elif any(k in title_lower for k in ['면담','상담','회의','미팅','학부모']):
        return "상담/회의"
    else:
        return "일반"


# ==========================================================
# 일정 삭제
# ==========================================================
async def handle_event_delete(message: str, db: Session):
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
        query = query.filter(title_condition)
    if event_date:
        query = query.filter(EventModel.date == event_date)
    
    events_to_delete = query.all()
    if not events_to_delete:
        return f"'{event_title or event_date}' 일정을 찾을 수 없습니다."
    
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
    clean_message = re.sub(r'(삭제|지워|취소|제거).*', '', message)
    clean_message = re.sub(r'일정\s*', '', clean_message)
    clean_message = re.sub(r'(내일|모레|오늘|다음\s*주|이번\s*주)', '', clean_message)
    clean_message = re.sub(r'\d{1,2}월\s*\d{1,2}일', '', clean_message)
    clean_message = re.sub(r'\d{1,2}일', '', clean_message)
    clean_message = re.sub(r'[을를이에의]', '', clean_message)
    return clean_message.strip() if clean_message and len(clean_message) > 1 else None

async def extract_event_date_for_delete(message: str) -> str:
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


# ==========================================================
# AI 기반 Query 처리 (기간+유형)
# ==========================================================
async def handle_event_ai_query(period: str, event_type: str, message: str, db: Session):
    today = datetime.now().date()
    query = db.query(EventModel)

    if period == "today":
        query = query.filter(EventModel.date == today)
    elif period == "week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        query = query.filter(EventModel.date.between(start, end))
    elif period == "month":
        query = query.filter(func.year(EventModel.date) == today.year)
        query = query.filter(func.month(EventModel.date) == today.month)

    if event_type and event_type != "일반":
        query = query.filter(EventModel.event_type == event_type)

    events = query.all()
    return await build_ai_response(events, message)
