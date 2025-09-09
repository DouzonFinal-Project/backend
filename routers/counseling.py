from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.db import SessionLocal
from models.students import Student as StudentModel
from models.meetings import Meeting as MeetingModel
from schemas.meetings import Meeting, MeetingCreate

router = APIRouter(prefix="/counseling", tags=["counseling"])

# ==========================================================
# [공통] DB 세션 관리
# ==========================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================
# [1단계] 학생별 상담 요약
# ==========================================================

# ✅ [READ] 학생 목록 + 상담 요약
@router.get("/students")
def get_students_with_summary(db: Session = Depends(get_db)):
    students = db.query(StudentModel).all()
    result = []

    for s in students:
        counseling_count = db.query(func.count(MeetingModel.id)) \
            .filter(MeetingModel.student_id == s.id).scalar()

        recent_date = db.query(func.max(MeetingModel.date)) \
            .filter(MeetingModel.student_id == s.id).scalar()

        recent_meeting = db.query(MeetingModel) \
            .filter(MeetingModel.student_id == s.id) \
            .order_by(MeetingModel.date.desc(), MeetingModel.time.desc()).first()

        result.append({
            "id": s.id,
            "name": s.student_name,   # ✅ student_name 컬럼 사용
            "class_id": s.class_id,
            "gender": s.gender,
            "phone": s.phone,
            "address": s.address,
            "counseling_count": counseling_count,
            "recent_date": recent_date,
            "recent_type": recent_meeting.meeting_type if recent_meeting else None,
            "recent_title": recent_meeting.title if recent_meeting else None,
        })

    return {"success": True, "data": result}


# ==========================================================
# [2단계] 상담 현황 통계
# ==========================================================

# ✅ [READ] 상담 통계
@router.get("/stats")
def get_counseling_stats(db: Session = Depends(get_db)):
    total_students = db.query(func.count(StudentModel.id)).scalar()
    students_with_counseling = db.query(MeetingModel.student_id).distinct().count()
    no_counseling = total_students - students_with_counseling

    focus_count = db.query(func.count(MeetingModel.id)) \
        .filter(MeetingModel.meeting_type == "집중관리").scalar()

    return {
        "success": True,
        "data": {
            "total_students": total_students,
            "counseling_completed": students_with_counseling,
            "focus_students": focus_count,
            "no_counseling": no_counseling
        }
    }


# ==========================================================
# [3단계] 상담 히스토리
# ==========================================================

# ✅ [READ] 특정 학생 상담 히스토리
@router.get("/history/{student_id}")
def get_student_history(student_id: int, db: Session = Depends(get_db)):
    history = db.query(MeetingModel) \
        .filter(MeetingModel.student_id == student_id) \
        .order_by(MeetingModel.date.desc(), MeetingModel.time.desc()).all()

    if not history:
        return {"success": False, "error": {"code": 404, "message": "상담 기록 없음"}}

    return {
        "success": True,
        "data": [
            {
                "id": h.id,
                "title": h.title,
                "meeting_type": h.meeting_type,
                "date": h.date,
                "time": h.time,
                "location": h.location,
                "teacher_id": h.teacher_id
            } for h in history
        ]
    }


# ==========================================================
# [4단계] 상담일지 작성
# ==========================================================

# ✅ [CREATE] 상담일지 저장
@router.post("/")
def create_counseling_entry(new_meeting: MeetingCreate, db: Session = Depends(get_db)):
    db_meeting = MeetingModel(**new_meeting.model_dump())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)

    return {
        "success": True,
        "data": {
            "id": db_meeting.id,
            "title": db_meeting.title,
            "meeting_type": db_meeting.meeting_type,
            "student_id": db_meeting.student_id,
            "teacher_id": db_meeting.teacher_id,
            "date": db_meeting.date,
            "time": db_meeting.time,
            "location": db_meeting.location,
            "message": "Counseling record created successfully"
        }
    }


# ==========================================================
# [5단계] AI 상담일지 미리보기 (Mock)
# ==========================================================

# ✅ [READ] AI 상담일지 생성 미리보기
@router.post("/ai-preview")
def ai_preview_counseling(content: str):
    return {
        "success": True,
        "data": {
            "preview": f"🤖 AI 상담일지 요약: {content[:50]}..."
        }
    }
