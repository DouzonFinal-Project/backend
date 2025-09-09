from sqlalchemy.orm import Session
from models.teachers import Teacher as TeacherModel
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings

# LangChain Gemini API 설정
model = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7
)

async def handle_teacher_query(message: str, db: Session):
    """교사 명단 조회 처리"""
    # 교사 데이터 조회
    teachers = db.query(TeacherModel).all()
    
    if not teachers:
        return "현재 등록된 선생님이 없습니다."
    
    # 교사 정보를 텍스트로 변환
    teacher_info = []
    for teacher in teachers:
        teacher_info.append(f"{teacher.name} 선생님 ({teacher.subject} 담당)")
    
    teacher_list = "\n".join([f"{i+1}. {info}" for i, info in enumerate(teacher_info)])
    
    # AI에게 전달할 프롬프트 생성
    prompt = f"""
    다음은 학교에 등록된 선생님 명단입니다:
    
    {teacher_list}
    
    사용자가 "{message}"라고 질문했습니다. 
    위 정보를 바탕으로 친근하고 자연스러운 한국어로 답변해주세요.
    """
    
    # Gemini API 호출
    response = await model.ainvoke(prompt)
    
    return response.content 