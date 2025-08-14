from sqlalchemy.orm import Session
from models.events import Event as EventModel
from datetime import datetime, timedelta
import re

def classify_event_type(content):
    """일정 유형 분류"""
    content_lower = content.lower()
    
    # 시험/평가
    if any(keyword in content_lower for keyword in ["시험", "고사", "평가", "중간", "기말", "모의고사", "수능"]):
        return "시험/평가"
    
    # 행사/활동
    elif any(keyword in content_lower for keyword in ["운동회", "체육대회", "행사", "활동", "축제", "문화제", "체육", "운동"]):
        return "행사/활동"
    
    # 상담/회의
    elif any(keyword in content_lower for keyword in ["상담", "회의", "면담", "학부모", "교사회의"]):
        return "상담/회의"
    
    # 캠페인
    elif any(keyword in content_lower for keyword in ["캠페인", "홍보", "안전", "환경"]):
        return "캠페인"
    
    # 예방교육
    elif any(keyword in content_lower for keyword in ["예방", "교육", "안전교육", "성교육"]):
        return "예방교육"
    
    # 업무회의
    elif any(keyword in content_lower for keyword in ["업무", "회의", "교직원"]):
        return "업무회의"
    
    # 기본값
    else:
        return "일반"

def parse_date(date_text):
    """날짜 파싱"""
    today = datetime.now()
    
    if "오늘" in date_text:
        return today.date()
    elif "내일" in date_text:
        return (today + timedelta(days=1)).date()
    elif "모레" in date_text:
        return (today + timedelta(days=2)).date()
    elif "다음주" in date_text:
        # 다음주 월요일
        days_ahead = 7 - today.weekday()
        return (today + timedelta(days=days_ahead)).date()
    
    # 특정 날짜 패턴 (예: 12월 15일, 12/15)
    date_patterns = [
        r'(\d{1,2})월\s*(\d{1,2})일',
        r'(\d{1,2})/(\d{1,2})',
        r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, date_text)
        if match:
            if len(match.groups()) == 2:  # 월/일
                month, day = int(match.group(1)), int(match.group(2))
                year = today.year
                # 과거 날짜면 다음해로 설정
                if month < today.month or (month == today.month and day < today.day):
                    year += 1
                return datetime(year, month, day).date()
            elif len(match.groups()) == 3:  # 년/월/일
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                return datetime(year, month, day).date()
    
    return None

def extract_event_content(message):
    """일정 내용 추출 (날짜 부분 제거)"""
    # 정규식으로 날짜 패턴 제거
    date_patterns = [
        r'\d{1,2}월\s*\d{1,2}일',
        r'\d{1,2}/\d{1,2}',
        r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일',
        r'\d{1,2}\s*\d{1,2}'  # "12 15" 같은 패턴
    ]
    
    content = message
    for pattern in date_patterns:
        content = re.sub(pattern, '', content)
    
    # 날짜 관련 키워드 제거
    date_keywords = ["오늘", "내일", "모레", "다음주", "월", "일", "년"]
    for keyword in date_keywords:
        content = content.replace(keyword, "")
    
    # "일정 추가" 등 키워드 제거
    remove_keywords = ["일정 추가", "일정 등록", "스케줄 추가", "등록", "추가", "를", "을", "해줘", "해주세요"]
    for keyword in remove_keywords:
        content = content.replace(keyword, "")
    
    # 조사/전치사 제거
    particles = ["정", "에", "의", "가", "이", "은", "는", "도", "만", "부터", "까지", "에서", "로", "으로"]
    for particle in particles:
        content = content.replace(particle, "")
    
    # 연속된 공백 제거 및 앞뒤 공백 제거
    content = re.sub(r'\s+', ' ', content).strip()
    
    return content.strip()

def handle_schedule_add(message: str, db: Session):
    """일정 추가 처리"""
    # 날짜 파싱
    event_date = parse_date(message)
    if not event_date:
        return "날짜를 인식할 수 없습니다. (예: 내일, 12월 15일, 다음주 월요일)"
    
    # 일정 내용 추출
    event_content = extract_event_content(message)
    if not event_content:
        return "일정 내용을 입력해주세요. (예: 내일 수학시험)"
    
    # 일정 유형 분류
    event_type = classify_event_type(event_content)
    
    # 일정 저장
    try:
        new_event = EventModel(
            date=event_date,
            event_name=event_content,
            description=f"AI를 통해 추가된 일정: {event_content}",
            event_type=event_type
        )
        db.add(new_event)
        db.commit()
        
        return f"{event_date.strftime('%m월 %d일')}에 '{event_content}' 일정이 성공적으로 추가되었습니다."
        
    except Exception as e:
        db.rollback()
        return f"일정 추가 중 오류가 발생했습니다: {str(e)}" 