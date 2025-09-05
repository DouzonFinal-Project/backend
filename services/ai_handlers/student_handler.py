from sqlalchemy.orm import Session
from models.students import Student as StudentModel
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings

# LangChain Gemini API 설정
model = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7
)

async def handle_student_query(message: str, db: Session):
    """학생 명단 조회 처리"""
    # 학생 데이터 조회
    students = db.query(StudentModel).all()
    
    if not students:
        return "현재 등록된 학생이 없습니다."
    
    # 학생 정보를 텍스트로 변환
    student_info = []
    for student in students:
        student_info.append(f"{student.student_name} ({student.class_id}반, {student.gender})")
    
    student_list = "\n".join([f"{i+1}. {info}" for i, info in enumerate(student_info)])
    
    # AI에게 전달할 프롬프트 생성
    prompt = f"""
    다음은 학교에 등록된 학생 명단입니다:
    
    {student_list}
    
    사용자가 "{message}"라고 질문했습니다. 
    위 정보를 바탕으로 친근하고 자연스러운 한국어로 답변해주세요.
    """
    
    # Gemini API 호출
    response = await model.ainvoke(prompt)
    
    return response.content 