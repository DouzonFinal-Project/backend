from sqlalchemy.orm import Session
from models.students import Student as StudentModel
from models.grades import Grade as GradeModel
from models.test_scores import TestScore as TestScoreModel
from models.subjects import Subject as SubjectModel
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings

# LangChain Gemini API 설정
model = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7
)

async def handle_grade_query(message: str, db: Session):
    """성적 조회 처리"""
    # 학생 이름 추출 (간단한 방식)
    student_name = None
    for word in message.split():
        if word.endswith("의") or word.endswith("이") or word.endswith("가"):
            student_name = word[:-1]  # "의", "이", "가" 제거
            break
    
    if not student_name:
        return "어떤 학생의 성적을 알고 싶으신가요? (예: 이예은의 성적을 알려줘)"
    
    # 학생 정보 조회
    student = db.query(StudentModel).filter(StudentModel.student_name == student_name).first()
    if not student:
        return f"'{student_name}' 학생을 찾을 수 없습니다."
    
    # 성적 정보 조회 (grades 테이블만 - 중간고사, 기말고사)
    grades = db.query(GradeModel).filter(GradeModel.student_id == student.id).all()
    
    if not grades:
        return f"'{student_name}' 학생의 성적 정보가 없습니다."
    
    # 성적 정보를 텍스트로 변환 (중간고사, 기말고사만)
    grade_info = []
    for grade in grades:
        # 과목명 조회
        subject = db.query(SubjectModel).filter(SubjectModel.id == grade.subject_id).first()
        subject_name = subject.name if subject else f"과목ID {grade.subject_id}"
        
        # term에 따른 시험 구분 (1: 중간고사, 2: 기말고사)
        term_name = "중간고사" if grade.term == 1 else "기말고사" if grade.term == 2 else f"{grade.term}학기"
        grade_info.append(f"• {subject_name}: {term_name} {grade.average_score}점 (등급: {grade.grade_letter})")
    
    grade_list = "\n".join(grade_info)
    
    # AI에게 전달할 프롬프트 생성
    prompt = f"""
    다음은 {student_name} 학생의 성적 정보입니다 (중간고사, 기말고사만):
    
    {grade_list}
    
    사용자가 "{message}"라고 질문했습니다. 
    위 정보를 바탕으로 간결하고 명확한 한국어로 답변해주세요.
    
    답변 형식:
    - 먼저 과목별로 중간고사와 기말고사 성적을 간단히 제시
    - 성적 정보 아래에 전체적인 학습 상황에 대한 간단한 피드백 추가 (2-3문장)
    - 이모지나 마크다운 형식 사용 금지
    - 일반 텍스트로만 답변
    - 예시: 
    "국어: 중간고사 62점(D), 기말고사 83점(B)
    수학: 중간고사 69점(D), 기말고사 99점(A+)
    
    전체적으로 기말고사에서 대부분 과목에서 향상된 모습을 보이고 있습니다. 특히 수학에서 큰 발전이 있었습니다."
    """
    
    # Gemini API 호출
    response = await model.ainvoke(prompt)
    
    return response.content 