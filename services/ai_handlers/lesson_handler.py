from sqlalchemy.orm import Session
from models.lessons import Lesson as LessonModel
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy import func, and_
from config.settings import settings
from datetime import datetime, timedelta
import re

# LangChain Gemini API 설정
model = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7
)


async def handle_lesson_query(message: str, db: Session):
    """수업 정보 조회 및 관리 처리"""
    user_message = message.lower()
    
    # 다음 수업 조회
    if any(keyword in user_message for keyword in ["다음 수업", "다음시간", "다음 교시", "다음시간표"]):
        return await handle_next_lesson(message, db)
    
    # 오늘 수업 조회
    if "오늘" in user_message and any(keyword in user_message for keyword in ["수업", "시간표", "교시"]):
        today = datetime.now().date()
        return await handle_today_lessons(today, message, db)
    
    # 특정 과목 수업 조회
    subject_keywords = ["수학", "국어", "영어", "과학", "사회", "체육", "음악", "미술"]
    for subject in subject_keywords:
        if subject in user_message:
            return await handle_subject_lesson(subject, message, db)
    
    # 기본: 다음 수업 조회
    return await handle_next_lesson(message, db)


async def handle_next_lesson(message: str, db: Session):
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
        
        return await build_next_lesson_response(next_lesson, message, is_tomorrow=True)
    
    return await build_next_lesson_response(next_lesson, message, is_tomorrow=False)


async def handle_today_lessons(date, message: str, db: Session):
    """오늘 수업 조회"""
    lessons = (
        db.query(LessonModel)
        .filter(LessonModel.date == date)
        .order_by(LessonModel.start_time)
        .all()
    )
    
    if not lessons:
        return f"오늘({date.strftime('%m월 %d일')}) 등록된 수업이 없습니다."
    
    return await build_today_lessons_response(lessons, message, date)


async def handle_subject_lesson(subject: str, message: str, db: Session):
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
    
    return await build_subject_lesson_response(lesson, message)


async def build_next_lesson_response(lesson, message: str, is_tomorrow: bool = False):
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
        lesson_info += f"\nPPT 자료 링크: {lesson.ppt_link}"
    
    time_info = "내일" if is_tomorrow else "오늘"
    
    prompt = f"""
    현재 날짜: {current_date}
    
    다음은 {time_info}의 다음 수업 정보입니다:
    
    {lesson_info}
    
    사용자가 "{message}"라고 질문했습니다. 
    
    다음 지침에 따라 답변해주세요:
    1. 별표(*) 기호를 사용하지 마세요
    2. 간결하고 전문적인 톤으로 답변하세요
    3. 존댓말을 사용하되 자연스럽게 하세요
    4. 수업 준비에 도움이 되는 실용적인 정보를 포함하세요
    5. 불필요한 반복을 피하고 핵심 정보에 집중하세요
    6. PPT 자료가 있다면 "수업에 사용될 PPT 자료는 아래에서 확인하실 수 있습니다:"라는 문구로 안내하세요
    """
    
    response = await model.ainvoke(prompt)
    return response.content


async def build_today_lessons_response(lessons, message: str, date):
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
            lesson_info += f"\nPPT 자료 링크: {lesson.ppt_link}"
        lessons_info.append(lesson_info)
    
    lessons_text = "\n---\n".join(lessons_info)
    
    prompt = f"""
    현재 날짜: {current_date}
    
    다음은 오늘의 수업 일정입니다:
    
    {lessons_text}
    
    사용자가 "{message}"라고 질문했습니다. 
    
    다음 지침에 따라 답변해주세요:
    1. 별표(*) 기호를 사용하지 마세요
    2. 간결하고 전문적인 톤으로 답변하세요
    3. 존댓말을 사용하되 자연스럽게 하세요
    4. 오늘 수업 일정을 체계적으로 정리해주세요
    5. 불필요한 반복을 피하고 핵심 정보에 집중하세요
    6. PPT 자료가 있다면 "수업에 사용될 PPT 자료는 아래 링크에서 확인하실 수 있습니다:"라는 문구로 안내하세요
    """
    
    response = await model.ainvoke(prompt)
    return response.content


async def build_subject_lesson_response(lesson, message: str):
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
        lesson_info += f"\nPPT 자료 링크: {lesson.ppt_link}"
    
    prompt = f"""
    현재 날짜: {current_date}
    
    다음은 {lesson.subject_name} 수업 정보입니다:
    
    {lesson_info}
    
    사용자가 "{message}"라고 질문했습니다. 
    
    다음 지침에 따라 답변해주세요:
    1. 별표(*) 기호를 사용하지 마세요
    2. 간결하고 전문적인 톤으로 답변하세요
    3. 존댓말을 사용하되 자연스럽게 하세요
    4. 불필요한 반복을 피하고 핵심 정보에 집중하세요
    5. PPT 자료가 있다면 "수업에 사용될 PPT 자료는 아래 링크에서 확인하실 수 있습니다:"라는 문구로 안내하세요
    """
    
    response = await model.ainvoke(prompt)
    return response.content 