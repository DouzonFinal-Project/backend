from sqlalchemy.orm import Session
from models.lessons import Lesson as LessonModel
import google.generativeai as genai
from sqlalchemy import func, and_
from config.settings import settings
from datetime import datetime, timedelta
import re

# Gemini API 설정
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)


def handle_lesson_query(message: str, db: Session):
    """수업 정보 조회 및 관리 처리"""
    user_message = message.lower()
    
    # 다음 수업 조회
    if any(keyword in user_message for keyword in ["다음 수업", "다음시간", "다음 교시", "다음시간표"]):
        return handle_next_lesson(message, db)
    
    # 오늘 수업 조회
    if "오늘" in user_message and any(keyword in user_message for keyword in ["수업", "시간표", "교시"]):
        today = datetime.now().date()
        return handle_today_lessons(today, message, db)
    
    # 특정 과목 수업 조회
    subject_keywords = ["수학", "국어", "영어", "과학", "사회", "체육", "음악", "미술"]
    for subject in subject_keywords:
        if subject in user_message:
            return handle_subject_lesson(subject, message, db)
    
    # 기본: 다음 수업 조회
    return handle_next_lesson(message, db)


def handle_next_lesson(message: str, db: Session):
    """다음 수업 조회"""
    current_time = datetime.now()
    current_date = current_time.date()
    current_time_str = current_time.strftime('%H:%M')
    
    # 오늘 날짜의 다음 수업 찾기
    next_lesson = (
        db.query(LessonModel)
        .filter(
            and_(
                LessonModel.date == current_date,
                LessonModel.start_time > current_time_str
            )
        )
        .order_by(LessonModel.start_time)
        .first()
    )
    
    if not next_lesson:
        # 오늘 남은 수업이 없으면 내일 첫 수업 찾기
        tomorrow = current_date + timedelta(days=1)
        next_lesson = (
            db.query(LessonModel)
            .filter(LessonModel.date == tomorrow)
            .order_by(LessonModel.start_time)
            .first()
        )
        
        if not next_lesson:
            return "다음 수업 일정이 등록되어 있지 않습니다."
        
        return build_next_lesson_response(next_lesson, message, is_tomorrow=True)
    
    return build_next_lesson_response(next_lesson, message, is_tomorrow=False)


def handle_today_lessons(date, message: str, db: Session):
    """오늘 수업 조회"""
    lessons = (
        db.query(LessonModel)
        .filter(LessonModel.date == date)
        .order_by(LessonModel.start_time)
        .all()
    )
    
    if not lessons:
        return f"오늘({date.strftime('%m월 %d일')}) 등록된 수업이 없습니다."
    
    return build_today_lessons_response(lessons, message, date)


def handle_subject_lesson(subject: str, message: str, db: Session):
    """특정 과목 수업 조회"""
    current_date = datetime.now().date()
    
    lesson = (
        db.query(LessonModel)
        .filter(
            and_(
                LessonModel.subject_name == subject,
                LessonModel.date >= current_date
            )
        )
        .order_by(LessonModel.date, LessonModel.start_time)
        .first()
    )
    
    if not lesson:
        return f"{subject} 수업 일정이 등록되어 있지 않습니다."
    
    return build_subject_lesson_response(lesson, message)


def build_next_lesson_response(lesson, message: str, is_tomorrow: bool = False):
    """다음 수업 응답 생성"""
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    
    lesson_info = f"""
    과목: {lesson.subject_name}
    제목: {lesson.lesson_title}
    내용: {lesson.lesson_content}
    시간: {lesson.start_time} ~ {lesson.end_time}
    교시: {lesson.lesson_time}
    """
    
    if lesson.ppt_link:
        lesson_info += f"PPT: {lesson.ppt_link}"
    
    time_info = "내일" if is_tomorrow else "오늘"
    
    prompt = f"""
    현재 날짜: {current_date}
    
    다음은 {time_info}의 다음 수업 정보입니다:
    
    {lesson_info}
    
    사용자가 "{message}"라고 질문했습니다. 
    위 정보를 바탕으로 친근하고 자연스러운 한국어로 답변해주세요.
    수업 준비에 도움이 되도록 실용적인 정보를 포함해주세요.
    """
    
    response = model.generate_content(prompt)
    return response.text


def build_today_lessons_response(lessons, message: str, date):
    """오늘 수업 목록 응답 생성"""
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    
    lessons_info = []
    for lesson in lessons:
        lesson_info = f"""
        {lesson.lesson_time} ({lesson.start_time}~{lesson.end_time})
        과목: {lesson.subject_name}
        제목: {lesson.lesson_title}
        내용: {lesson.lesson_content}
        """
        if lesson.ppt_link:
            lesson_info += f"PPT: {lesson.ppt_link}"
        lessons_info.append(lesson_info)
    
    lessons_text = "\n---\n".join(lessons_info)
    
    prompt = f"""
    현재 날짜: {current_date}
    
    다음은 오늘의 수업 일정입니다:
    
    {lessons_text}
    
    사용자가 "{message}"라고 질문했습니다. 
    위 정보를 바탕으로 친근하고 자연스러운 한국어로 답변해주세요.
    오늘 수업 일정을 정리해서 보기 쉽게 설명해주세요.
    """
    
    response = model.generate_content(prompt)
    return response.text


def build_subject_lesson_response(lesson, message: str):
    """특정 과목 수업 응답 생성"""
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    
    lesson_info = f"""
    과목: {lesson.subject_name}
    제목: {lesson.lesson_title}
    내용: {lesson.lesson_content}
    날짜: {lesson.date.strftime('%m월 %d일')}
    시간: {lesson.start_time} ~ {lesson.end_time}
    교시: {lesson.lesson_time}
    """
    
    if lesson.ppt_link:
        lesson_info += f"PPT: {lesson.ppt_link}"
    
    prompt = f"""
    현재 날짜: {current_date}
    
    다음은 {lesson.subject_name} 수업 정보입니다:
    
    {lesson_info}
    
    사용자가 "{message}"라고 질문했습니다. 
    위 정보를 바탕으로 친근하고 자연스러운 한국어로 답변해주세요.
    """
    
    response = model.generate_content(prompt)
    return response.text 