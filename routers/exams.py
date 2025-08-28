from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import SessionLocal
# (DB 저장 여부에 따라 models/schemas 연동 가능)
# from models.exams import Exam as ExamModel
# from schemas.exams import ExamCreate

# ✅ AI 핸들러 (문제 생성 호출)
from services.ai_handlers import exam_handler  

router = APIRouter(prefix="/exams", tags=["시험지 생성 및 관리"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ [GENERATE] 시험지 자동 생성 (AI 연동)
@router.post("/generate")
async def generate_exam(payload: dict, db: Session = Depends(get_db)):
    """
    시험지 자동 생성 API
    - 입력: {"subject": "국어", "unit": "4단원", "level": "중급", "question_count": 10, "types": ["어휘", "내용이해"]}
    - 처리: AI 핸들러 호출
    - 출력: 생성된 문제 리스트 반환
    """
    result = await exam_handler.generate_exam(payload, db)
    return {
        "success": True,
        "data": result,
        "message": "시험지가 성공적으로 생성되었습니다"
    }

  
################## 주석 처리 ##################
# ----------------------------------------------------
# 📌 시험지 DB 저장/조회/삭제 관련 기능 (현재 미사용)
#    필요 시 주석 해제 후 사용 가능
# ----------------------------------------------------

'''
# ✅ [CREATE] 시험지 저장
@router.post("/")
def create_exam(exam_data: dict, db: Session = Depends(get_db)):
    """
    생성된 시험지를 DB에 저장 (옵션)
    """
    # db_exam = ExamModel(**exam_data)
    # db.add(db_exam)
    # db.commit()
    # db.refresh(db_exam)
    return {
        "success": True,
        "data": exam_data,
        "message": "시험지가 성공적으로 저장되었습니다"
    }


# ✅ [READ] 전체 시험지 목록 조회
@router.get("/")
def read_exams(db: Session = Depends(get_db)):
    """
    저장된 시험지 목록 조회
    """
    # records = db.query(ExamModel).all()
    # return [{"id": r.id, "title": r.title, "subject": r.subject} for r in records]
    return {
        "success": True,
        "data": [],
        "message": "전체 시험지 목록 조회 완료"
    }


# ✅ [READ] 특정 시험지 조회
@router.get("/{exam_id}")
def read_exam(exam_id: int, db: Session = Depends(get_db)):
    """
    특정 시험지 상세 조회
    """
    # exam = db.query(ExamModel).filter(ExamModel.id == exam_id).first()
    # if exam is None:
    #     return {"success": False, "error": {"code": 404, "message": "시험지를 찾을 수 없습니다"}}
    return {
        "success": True,
        "data": {"exam_id": exam_id},
        "message": "시험지 상세 조회 성공"
    }


# ✅ [DELETE] 시험지 삭제
@router.delete("/{exam_id}")
def delete_exam(exam_id: int, db: Session = Depends(get_db)):
    """
    특정 시험지 삭제
    """
    # exam = db.query(ExamModel).filter(ExamModel.id == exam_id).first()
    # if exam is None:
    #     return {"success": False, "error": {"code": 404, "message": "시험지를 찾을 수 없습니다"}}
    # db.delete(exam)
    # db.commit()
    return {
        "success": True,
        "data": {"exam_id": exam_id},
        "message": "시험지가 성공적으로 삭제되었습니다"
    }
'''