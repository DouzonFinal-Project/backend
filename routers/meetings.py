from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from database.db import SessionLocal
from models.meetings import Meeting as MeetingModel
from schemas.meetings import Meeting as MeetingSchema, MeetingCreate
from datetime import date, timedelta

router = APIRouter(prefix="/meetings", tags=["상담 기록"])

# ==========================================================
# [DB 종속성 주입] 세션 연결
# ==========================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================
# [1단계] CRUD 기본 라우터
# ==========================================================

# ✅ [CREATE] 상담 기록 추가
@router.post("/")
def create_meeting(meeting: MeetingCreate, db: Session = Depends(get_db)):
    db_meeting = MeetingModel(**meeting.model_dump())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return {
        "success": True,
        "data": db_meeting.__dict__,
        "message": "상담 기록이 성공적으로 추가되었습니다"
    }


# ✅ [READ] 전체 상담 기록 조회
@router.get("/")
def read_meetings(db: Session = Depends(get_db)):
    records = db.query(MeetingModel).all()
    return {
        "success": True,
        "data": [r.__dict__ for r in records],
        "message": "전체 상담 기록 조회 완료"
    }


# ==========================================================
# [2단계] 정적 라우터
# ==========================================================

# ✅ [SUMMARY] 상담 전체 요약 통계
@router.get("/summary")
def meetings_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(MeetingModel.id)).scalar()
    latest = db.query(func.max(MeetingModel.date)).scalar()
    return {
        "success": True,
        "data": {"총 상담 건수": total, "최근 상담일": str(latest) if latest else None},
        "message": "상담 기록 요약 통계 조회 완료"
    }


# ✅ [READ] 특정 교사 상담 기록 조회
@router.get("/teacher/{teacher_id}")
def get_meetings_by_teacher(teacher_id: int, db: Session = Depends(get_db)):
    meetings = db.query(MeetingModel).filter(MeetingModel.teacher_id == teacher_id).all()
    if not meetings:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 교사의 상담 기록이 없습니다"}
        }
    return {
        "success": True,
        "data": [m.__dict__ for m in meetings],
        "message": f"교사 ID {teacher_id} 상담 기록 조회 성공"
    }


# ✅ [READ] 특정 학생 상담 기록 조회
@router.get("/student/{student_id}")
def get_meetings_by_student(student_id: int, db: Session = Depends(get_db)):
    meetings = db.query(MeetingModel).filter(MeetingModel.student_id == student_id).all()
    if not meetings:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 학생의 상담 기록이 없습니다"}
        }
    return {
        "success": True,
        "data": [m.__dict__ for m in meetings],
        "message": f"학생 ID {student_id} 상담 기록 조회 성공"
    }


# ==========================================================
# [3단계] 혼합 라우터
# ==========================================================

# ✅ [READ] 특정 월 상담 기록 조회
@router.get("/monthly/{year}/{month}")
def get_meetings_by_month(year: int, month: int, db: Session = Depends(get_db)):
    meetings = db.query(MeetingModel).filter(
        extract("year", MeetingModel.date) == year,
        extract("month", MeetingModel.date) == month
    ).all()
    if not meetings:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 월의 상담 기록이 없습니다"}
        }
    return {
        "success": True,
        "data": [m.__dict__ for m in meetings],
        "message": f"{year}년 {month}월 상담 기록 조회 성공"
    }


# ✅ [STATS] 이번 주 상담 건수 통계
@router.get("/stats/weekly")
def get_weekly_meeting_stats(db: Session = Depends(get_db)):
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())   # 이번 주 월요일
    end_of_week = start_of_week + timedelta(days=6)           # 이번 주 일요일

    count = (
        db.query(func.count(MeetingModel.id))
        .filter(MeetingModel.date >= start_of_week, MeetingModel.date <= end_of_week)
        .scalar()
    )

    return {
        "success": True,
        "data": {
            "week": f"{start_of_week} ~ {end_of_week}",
            "weekly_meeting_count": count
        },
        "message": "이번 주 상담 건수 통계 조회 성공"
    }



# ✅ [STATS] 교사별 상담 건수 통계
@router.get("/stats/teacher/{teacher_id}")
def get_teacher_meeting_stats(teacher_id: int, db: Session = Depends(get_db)):
    count = db.query(func.count(MeetingModel.id)).filter(MeetingModel.teacher_id == teacher_id).scalar()
    return {
        "success": True,
        "data": {"교사 ID": teacher_id, "상담 건수": count},
        "message": f"교사 ID {teacher_id} 상담 건수 통계 조회 성공"
    }


# ✅ [STATS] 학생별 상담 건수/최종 상담일
@router.get("/stats/student/{student_id}")
def get_student_meeting_stats(student_id: int, db: Session = Depends(get_db)):
    total = db.query(func.count(MeetingModel.id)).filter(MeetingModel.student_id == student_id).scalar()
    last = db.query(func.max(MeetingModel.date)).filter(MeetingModel.student_id == student_id).scalar()
    return {
        "success": True,
        "data": {"학생 ID": student_id, "상담 건수": total, "최종 상담일": str(last) if last else None},
        "message": f"학생 ID {student_id} 상담 통계 조회 성공"
    }


# ==========================================================
# [4단계] 동적 라우터
# ==========================================================

# ✅ [READ] 상담 상세 조회
@router.get("/{meeting_id}")
def read_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    if meeting is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "상담 정보를 찾을 수 없습니다"}
        }
    return {
        "success": True,
        "data": meeting.__dict__,
        "message": "상담 기록 조회 성공"
    }


# ✅ [UPDATE] 상담 기록 수정
@router.put("/{meeting_id}")
def update_meeting(meeting_id: int, updated: MeetingCreate, db: Session = Depends(get_db)):
    meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    if meeting is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "상담 정보를 찾을 수 없습니다"}
        }

    for key, value in updated.model_dump().items():
        setattr(meeting, key, value)

    db.commit()
    db.refresh(meeting)
    return {
        "success": True,
        "data": meeting.__dict__,
        "message": "상담 기록이 성공적으로 수정되었습니다"
    }


# ✅ [DELETE] 상담 기록 삭제
@router.delete("/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    if meeting is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "상담 정보를 찾을 수 없습니다"}
        }

    db.delete(meeting)
    db.commit()
    return {
        "success": True,
        "data": {"meeting_id": meeting_id},
        "message": "상담 기록이 성공적으로 삭제되었습니다"
    }
