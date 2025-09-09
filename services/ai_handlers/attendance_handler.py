from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings
from models.attendance import Attendance as AttendanceModel
from models.students import Student as StudentModel
from sqlalchemy import func
from datetime import datetime, timedelta
import re

# ✅ LangChain Gemini API 설정
model = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7
)


async def handle_attendance_query(message: str, db: Session):
    """
    출결 관련 질의 처리
    - "이번주 결석한 학생 알려줘"
    """
    user_message = message.lower()

    # 이번 주 결석 학생 조회
    if ("이번주" in user_message or "이번 주" in user_message) and ("결석" in user_message):
        return await weekly_absent_students(message, db)

    # 기본 응답
    return "죄송합니다. 현재는 '이번주 결석한 학생 알려줘' 기능만 지원합니다."


async def weekly_absent_students(message: str, db: Session):
    """이번 주 결석한 학생 조회"""
    try:
        # 이번 주 날짜 범위 계산
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())  # 월요일
        end = start + timedelta(days=6)                  # 일요일
        
        # 결석한 학생 조회
        absent_students = (
            db.query(StudentModel, AttendanceModel)
            .join(AttendanceModel, StudentModel.id == AttendanceModel.student_id)
            .filter(
                AttendanceModel.date.between(start, end),
                AttendanceModel.status == '결석'
            )
            .all()
        )
        
        if not absent_students:
            return "이번 주에는 결석한 학생이 없습니다. 모든 학생이 출석했습니다! 👍"
        
        # 결석 학생 목록 생성
        absent_list = []
        for student, attendance in absent_students:
            reason_text = f" - {attendance.reason}" if attendance.reason else " - 사유 미기재"
            absent_list.append(f"{student.student_name} ({attendance.date}){reason_text}")
        
        # AI에게 전문가 챗봇 스타일 응답 생성 요청
        prompt = f"""
        다음은 이번 주 결석한 학생 목록입니다:
        {chr(10).join(absent_list)}
        
        전문가 챗봇처럼 깔끔하고 체계적으로 답변해주세요.
        제목은 ****제목**** 형태로 감싸서 작성해주세요:
        
        ****이번 주 출결 현황****
        결석 학생: X명
        주요 사유: 사유1, 사유2
        
        ****결석 학생 상세****
        • 학생명 (날짜) - 사유
        
        간결하고 전문적으로 작성해주세요.
        """
        
        response = await model.ainvoke(prompt)
        return response.content
        
    except Exception as e:
        return f"결석 학생 조회 중 오류가 발생했습니다: {str(e)}"
