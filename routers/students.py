from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.db import SessionLocal
from models.students import Student as StudentModel
from models.grades import Grade as GradeModel
from models.attendance import Attendance as AttendanceModel
from models.meetings import Meeting as MeetingModel
from schemas.students import StudentCreate

router = APIRouter(prefix="/students", tags=["학생 정보"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================
# [1단계] CRUD 기본 라우터
# ==========================================================

# ✅ [CREATE] 학생 정보 추가
@router.post("/")
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = StudentModel(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return {
        "success": True,
        "data": {
            "id": db_student.id,
            "student_name": db_student.student_name,
            "class_id": db_student.class_id,
            "gender": db_student.gender,
            "phone": db_student.phone,
            "address": db_student.address
        },
        "message": "학생 정보가 성공적으로 추가되었습니다"
    }


# ✅ [READ] 전체 학생 조회
@router.get("/")
def read_students(db: Session = Depends(get_db)):
    records = db.query(StudentModel).all()
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "student_name": r.student_name,
                "class_id": r.class_id,
                "gender": r.gender,
                "phone": r.phone,
                "address": r.address
            }
            for r in records
        ],
        "message": "전체 학생 정보 조회 완료"
    }


# ==========================================================
# [2단계] 정적 라우터 (검색/통계)
# ==========================================================

# ✅ [SEARCH] 이름으로 학생 검색
@router.get("/search")
def search_students(name: str = None, db: Session = Depends(get_db)):
    query = db.query(StudentModel)
    if name:
        query = query.filter(StudentModel.student_name.contains(name))
    results = query.all()
    if not results:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 조건의 학생을 찾을 수 없습니다"}
        }
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "student_name": r.student_name,
                "class_id": r.class_id,
                "gender": r.gender,
                "phone": r.phone,
                "address": r.address
            }
            for r in results
        ],
        "message": "학생 검색 결과 조회 성공"
    }


# ✅ [READ] 특정 반의 학생 목록 조회
@router.get("/class/{class_id}")
def get_students_by_class(class_id: int, db: Session = Depends(get_db)):
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 반에 학생이 없습니다"}
        }
    return {
        "success": True,
        "data": [
            {
                "id": s.id,
                "student_name": s.student_name,
                "class_id": s.class_id,
                "gender": s.gender,
                "phone": s.phone,
                "address": s.address
            }
            for s in students
        ],
        "message": f"반 ID {class_id} 학생 목록 조회 성공"
    }


# ✅ [SUMMARY] 전체/반별 학생 수 통계
@router.get("/summary")
def student_summary(db: Session = Depends(get_db)):
    total = db.query(StudentModel).count()
    by_class = db.query(StudentModel.class_id,
                        func.count(StudentModel.id)).group_by(StudentModel.class_id).all()
    return {
        "success": True,
        "data": {
            "total_students": total,
            "by_class": [{"class_id": c, "count": cnt} for c, cnt in by_class]
        },
        "message": "전체 및 반별 학생 수 통계 조회 성공"
    }


# ==========================================================
# [3단계] 혼합 라우터 (학생별 성적/출결/상담)
# ==========================================================

# ✅ [SUMMARY] 특정 학생 성적 요약
@router.get("/{student_id}/grade-summary")
def get_student_grade_summary(student_id: int, db: Session = Depends(get_db)):
    grades = db.query(GradeModel).filter(GradeModel.student_id == student_id).all()
    if not grades:
        return {
            "success": False,
            "error": {"code": 404, "message": "성적 정보가 없습니다"}
        }
    avg_score = sum([g.average_score for g in grades]) / len(grades)
    return {
        "success": True,
        "data": {
            "total_subjects": len(grades),
            "average_score": avg_score,
            "grades": [{"subject": g.subject_id, "score": g.average_score} for g in grades]
        },
        "message": f"학생 ID {student_id} 성적 요약 조회 성공"
    }


# ✅ [SUMMARY] 특정 학생 출결 요약
@router.get("/{student_id}/attendance-summary")
def get_student_attendance_summary(student_id: int, db: Session = Depends(get_db)):
    records = db.query(AttendanceModel).filter(AttendanceModel.student_id == student_id).all()
    if not records:
        return {
            "success": False,
            "error": {"code": 404, "message": "출결 기록이 없습니다"}
        }
    summary = {
        "present": sum(1 for r in records if r.status == "출석"),
        "absent": sum(1 for r in records if r.status == "결석"),
        "late": sum(1 for r in records if r.status == "지각")
    }
    return {
        "success": True,
        "data": summary,
        "message": f"학생 ID {student_id} 출결 요약 조회 성공"
    }


# ✅ [READ] 특정 학생 상담 기록 조회
@router.get("/{student_id}/meetings")
def get_student_meetings(student_id: int, db: Session = Depends(get_db)):
    meetings = db.query(MeetingModel).filter(MeetingModel.student_id == student_id).all()
    if not meetings:
        return {
            "success": False,
            "error": {"code": 404, "message": "상담 기록이 없습니다"}
        }
    return {
        "success": True,
        "data": [
            {
                "id": m.id,
                "title": m.title,
                "meeting_type": m.meeting_type,
                "date": str(m.date),
                "time": str(m.time),
                "location": m.location,
                "student_id": m.student_id,
                "teacher_id": m.teacher_id
            }
            for m in meetings
        ],
        "message": f"학생 ID {student_id} 상담 기록 조회 성공"
    }


# ==========================================================
# [4단계] 완전 동적 라우터 (개별 조회/수정/삭제)
# ==========================================================

# ✅ [READ] 특정 학생 상세 조회
@router.get("/{student_id}")
def read_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if student is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "학생 정보를 찾을 수 없습니다"}
        }
    return {
        "success": True,
        "data": {
            "id": student.id,
            "student_name": student.student_name,
            "class_id": student.class_id,
            "gender": student.gender,
            "phone": student.phone,
            "address": student.address
        },
        "message": "학생 상세 정보 조회 성공"
    }


# ✅ [UPDATE] 특정 학생 정보 수정
@router.put("/{student_id}")
def update_student(student_id: int, updated: StudentCreate, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if student is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "학생 정보를 찾을 수 없습니다"}
        }

    for key, value in updated.model_dump().items():
        setattr(student, key, value)

    db.commit()
    db.refresh(student)
    return {
        "success": True,
        "data": {
            "id": student.id,
            "student_name": student.student_name,
            "class_id": student.class_id,
            "gender": student.gender,
            "phone": student.phone,
            "address": student.address
        },
        "message": "학생 정보가 성공적으로 수정되었습니다"
    }


# ✅ [DELETE] 특정 학생 삭제
@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if student is None:
        return {
            "success": False,
            "error": {"code": 404, "message": "학생 정보를 찾을 수 없습니다"}
        }

    db.delete(student)
    db.commit()
    return {
        "success": True,
        "data": {"student_id": student_id},
        "message": "학생 정보가 성공적으로 삭제되었습니다"
    }
