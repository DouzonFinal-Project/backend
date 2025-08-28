from sqlalchemy.orm import Session
import google.generativeai as genai
from config.settings import settings
from models.attendance import Attendance as AttendanceModel
from sqlalchemy import func
from datetime import datetime, timedelta
import re

# ✅ Gemini API 설정
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)


def handle_attendance_query(message: str, db: Session):
    """
    출결 관련 질의 처리
    - "이번 주 출석 상황"
    - "이번 달 철수 출석률"
    - "3반 출석 요약"
    """
    user_message = message.lower()

    # 이번 주 출석
    if "이번주" in user_message or "이번 주" in user_message:
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())  # 월요일
        end = start + timedelta(days=6)                  # 일요일
        return weekly_summary(db, start, end, message)

    # 이번 달 출석
    if "이번달" in user_message or "이번 달" in user_message:
        year, month = datetime.now().year, datetime.now().month
        return monthly_summary(db, year, month, message)

    # 특정 학생 출석
    student_match = re.search(r'(\d+)번|(\w+) 학생', message)
    if student_match:
        # 여기서는 단순화해서 student_id 추출했다고 가정
        student_id = int(student_match.group(1)) if student_match.group(1) else None
        if student_id:
            return student_summary(db, student_id, message)

    # 특정 반 출석
    class_match = re.search(r'(\d+)반', message)
    if class_match:
        class_id = int(class_match.group(1))
        return class_summary(db, class_id, message)

    return "출석 관련 요청을 이해하지 못했습니다. 예: '이번주 3반 출석 알려줘'"


def weekly_summary(db: Session, start, end, message: str):
    records = (
        db.query(AttendanceModel)
        .filter(AttendanceModel.date.between(start, end))
        .all()
    )
    return build_ai_response(records, message)


def monthly_summary(db: Session, year: int, month: int, message: str):
    records = (
        db.query(AttendanceModel)
        .filter(func.year(AttendanceModel.date) == year)
        .filter(func.month(AttendanceModel.date) == month)
        .all()
    )
    return build_ai_response(records, message)


def student_summary(db: Session, student_id: int, message: str):
    records = (
        db.query(AttendanceModel)
        .filter(AttendanceModel.student_id == student_id)
        .all()
    )
    return build_ai_response(records, message)


def class_summary(db: Session, class_id: int, message: str):
    records = (
        db.query(AttendanceModel)
        .filter(AttendanceModel.class_id == class_id)
        .all()
    )
    return build_ai_response(records, message)


def build_ai_response(records, message: str):
    if not records:
        return "❌ 해당 조건에 맞는 출석 기록이 없습니다."

    record_info = [
        f"{r.date} - 학생 {r.student_id}: {r.status}" for r in records
    ]
    record_list = "\n".join(record_info)

    prompt = f"""
    다음은 출석 기록입니다:

    {record_list}

    사용자가 "{message}" 라고 물었습니다.
    위 정보를 바탕으로 한국어로 자연스럽게 요약하여 답변해 주세요.
    """

    response = model.generate_content(prompt)
    return response.text
