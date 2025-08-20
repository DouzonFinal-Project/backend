from sqlalchemy.orm import Session
from models.students import Student as StudentModel
from models.grades import Grade as GradeModel
from models.test_scores import TestScore as TestScoreModel
from models.subjects import Subject as SubjectModel
import google.generativeai as genai
from config.settings import settings

# Gemini API 설정
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)

def handle_grade_query(message: str, db: Session):
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
    
    # 성적 정보 조회 (grades 테이블)
    grades = db.query(GradeModel).filter(GradeModel.student_id == student.id).all()
    
    # 시험 성적 정보 조회 (test_scores 테이블)
    test_scores = db.query(TestScoreModel).filter(TestScoreModel.student_id == student.id).all()
    
    if not grades and not test_scores:
        return f"'{student_name}' 학생의 성적 정보가 없습니다."
    
    # 성적 정보를 텍스트로 변환
    grade_info = []
    if grades:
        grade_info.append("일반 성적:")
        for grade in grades:
            # 과목명 조회
            subject = db.query(SubjectModel).filter(SubjectModel.id == grade.subject_id).first()
            subject_name = subject.name if subject else f"과목ID {grade.subject_id}"
            grade_info.append(f"- {subject_name}: {grade.average_score}점 (등급: {grade.grade_letter})")
    
    if test_scores:
        if grade_info:
            grade_info.append("")
        grade_info.append("시험 성적:")
        for test_score in test_scores:
            grade_info.append(f"- {test_score.subject_name}: {test_score.score}점")
    
    grade_list = "\n".join(grade_info)
    
    # AI에게 전달할 프롬프트 생성
    prompt = f"""
    다음은 {student_name} 학생의 성적 정보입니다:
    
    {grade_list}
    
    사용자가 "{message}"라고 질문했습니다. 
    위 정보를 바탕으로 친근하고 자연스러운 한국어로 답변해주세요.
    성적이 좋으면 칭찬하고, 개선이 필요하면 격려하는 말을 포함해주세요.
    """
    
    # Gemini API 호출
    response = model.generate_content(prompt)
    
    return response.text 