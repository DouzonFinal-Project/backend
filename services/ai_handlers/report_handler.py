from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings

# LangChain Gemini API 설정
model = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7
)


def handle_report_query(message: str, db: Session):
    """
    학급/학생/학교 단위 통합 리포트 생성
    예: "이번 달 3반 리포트 만들어줘", "철수 학생 리포트", "학교 전체 리포트"
    """
    user_message = message.lower()

    # 기본 기간: 이번 달
    now = datetime.now()
    year, month = now.year, now.month

    if "지난달" in user_message:
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1

    # 반 리포트
    class_match = re.search(r'(\d+)반', message)
    if class_match:
        class_id = int(class_match.group(1))
        return build_class_report(db, year, month, class_id, message)

    # 학생 리포트
    student_match = re.search(r'(\w+)\s*학생', message)
    if student_match:
        student_name = student_match.group(1)
        return build_student_report(db, year, month, student_name, message)

    # 기본: 학교 전체 리포트
    return build_school_report(db, year, month, message)


# ---------------------------------------------------------------
# Class Report
# ---------------------------------------------------------------
def build_class_report(db: Session, year: int, month: int, class_id: int, message: str):
    grades = (
        db.query(GradeModel)
        .filter(GradeModel.class_id == class_id)
        .filter(func.extract("month", GradeModel.created_at) == month)
        .all()
    )
    attendance = (
        db.query(AttendanceModel)
        .filter(AttendanceModel.class_id == class_id)
        .filter(func.extract("month", AttendanceModel.date) == month)
        .all()
    )
    notices = (
        db.query(NoticeModel)
        .filter(func.extract("month", NoticeModel.created_at) == month)
        .all()
    )
    events = (
        db.query(EventModel)
        .filter(func.extract("month", EventModel.date) == month)
        .all()
    )

    return build_ai_report("📘 학급 리포트", grades, attendance, notices, events, message)


# ---------------------------------------------------------------
# Student Report
# ---------------------------------------------------------------
def build_student_report(db: Session, year: int, month: int, student_name: str, message: str):
    grades = (
        db.query(GradeModel)
        .filter(GradeModel.student_name == student_name)
        .filter(func.extract("month", GradeModel.created_at) == month)
        .all()
    )
    attendance = (
        db.query(AttendanceModel)
        .filter(AttendanceModel.student_name == student_name)
        .filter(func.extract("month", AttendanceModel.date) == month)
        .all()
    )
    # TODO: 상담 기록 모델 연결 필요시 여기에 추가
    return build_ai_report("👩‍🎓 학생 리포트", grades, attendance, [], [], message)


# ---------------------------------------------------------------
# School Report
# ---------------------------------------------------------------
def build_school_report(db: Session, year: int, month: int, message: str):
    notices = (
        db.query(NoticeModel)
        .filter(func.extract("month", NoticeModel.created_at) == month)
        .all()
    )
    events = (
        db.query(EventModel)
        .filter(func.extract("month", EventModel.date) == month)
        .all()
    )
    meetings = (
        db.query(MeetingModel)
        .filter(func.extract("month", MeetingModel.created_at) == month)
        .all()
    )
    return build_ai_report("🏫 학교 전체 리포트", [], [], notices, events, message, meetings)


# ---------------------------------------------------------------
# AI Report Generator
# ---------------------------------------------------------------
def build_ai_report(title: str, grades, attendance, notices, events, message: str, meetings=None):
    grade_info = (
        "\n".join([f"{g.student_name} - {g.subject}: {g.score}" for g in grades])
        if grades else "데이터 없음"
    )
    attendance_info = (
        "\n".join([f"{a.date} {a.student_name}: {a.status}" for a in attendance])
        if attendance else "데이터 없음"
    )
    notice_info = (
        "\n".join([f"{n.title} ({n.created_at.strftime('%Y-%m-%d')})" for n in notices])
        if notices else "데이터 없음"
    )
    event_info = (
        "\n".join([f"{e.event_name} ({e.date})" for e in events])
        if events else "데이터 없음"
    )
    meeting_info = (
        "\n".join([f"{m.title} ({m.created_at.strftime('%Y-%m-%d')})" for m in meetings])
        if meetings else "데이터 없음"
    )

    prompt = f"""
    {title}
    사용자가 "{message}" 라고 요청했습니다.

    다음 데이터를 종합해서 이번 기간에 대한 보고서를 작성해 주세요.
    - 데이터는 항목별 요약을 포함하고,
    - 성적, 출결, 공지사항, 이벤트, 회의록을 균형 있게 정리해 주세요.
    - 부족한 데이터가 있으면 "데이터 없음"으로 표시하고 넘어가세요.

    [성적 요약]
    {grade_info}

    [출결 요약]
    {attendance_info}

    [공지사항]
    {notice_info}

    [이벤트]
    {event_info}

    [회의록]
    {meeting_info}
    """

    response = model.invoke(prompt)
    return response.content
