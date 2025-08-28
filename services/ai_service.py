from sqlalchemy.orm import Session
from services.ai_handlers.teacher_handler import handle_teacher_query
from services.ai_handlers.student_handler import handle_student_query
from services.ai_handlers.grade_handler import handle_grade_query
from services.ai_handlers.event_handler import handle_event_query
from services.ai_handlers.notice_handler import handle_notice_query

def process_ai_query(message: str, db: Session):
    """AI 쿼리 처리 메인 함수"""
    user_message = message.lower()
    
    # 교사 명단 조회
    if any(keyword in user_message for keyword in ["선생님", "교사"]) and any(keyword in user_message for keyword in ["명단", "목록"]):
        return handle_teacher_query(message, db)
    
    # 학생 명단 조회
    elif any(keyword in user_message for keyword in ["학생"]) and any(keyword in user_message for keyword in ["명단", "목록"]):
        return handle_student_query(message, db)
    
    # 성적 조회
    elif "성적" in user_message:
        return handle_grade_query(message, db)
    
    # 이벤트/일정 조회 및 추가
    elif any(keyword in user_message for keyword in ["일정", "이벤트", "행사", "스케줄", "추가", "등록", "만들어"]):
        return handle_event_query(message, db)
    
    # 공지사항 조회
    elif any(keyword in user_message for keyword in ["공지", "공지사항", "알림"]):
        return handle_notice_query(message, db)
    
    # 기본 응답
    else:
        return "죄송합니다. 현재는 선생님/학생 명단 조회, 성적 조회, 이벤트/일정 조회 및 추가, 공지사항 조회, 수업 정보 조회 기능만 지원합니다." 