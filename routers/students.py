from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.db import SessionLocal
from models.students import Student as StudentModel
from models.grades import Grade as GradeModel
from models.attendance import Attendance as AttendanceModel
from models.meetings import Meeting as MeetingModel
from schemas.students import Student, StudentCreate

router = APIRouter(prefix="/students", tags=["학생 정보"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================================
# [1단계] CRUD 기본 라우터 - 루트 경로 우선 처리
# ==========================================================

# ✅ [CREATE] 학생 정보 추가
@router.post("/", response_model=Student)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = StudentModel(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# ✅ [READ] 전체 학생 조회
@router.get("/", response_model=list[Student])
def read_students(db: Session = Depends(get_db)):
    return db.query(StudentModel).all()

# ==========================================================
# [2단계] 정적 라우터 - 구체적인 경로들
# ==========================================================

# ✅ [SEARCH] 이름/학번으로 학생 검색
@router.get("/search", response_model=list[Student])
def search_students(
    name: str = Query(None, description="학생 이름"),
    student_no: str = Query(None, description="학번"),
    db: Session = Depends(get_db)
):
    query = db.query(StudentModel)
    if name:
        query = query.filter(StudentModel.student_name.contains(name))
    if student_no:
        query = query.filter(StudentModel.student_no == student_no)
    results = query.all()
    if not results:
        raise HTTPException(status_code=404, detail="해당 조건의 학생을 찾을 수 없습니다")
    return results

# ✅ [READ] 특정 반의 학생 목록 조회
@router.get("/class/{class_id}", response_model=list[Student])
def get_students_by_class(class_id: int, db: Session = Depends(get_db)):
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        raise HTTPException(status_code=404, detail="해당 반에 학생이 없습니다")
    return students

# ✅ [SUMMARY] 전체/반별 학생 수 통계
@router.get("/summary")
def student_summary(db: Session = Depends(get_db)):
    total = db.query(StudentModel).count()
    by_class = db.query(StudentModel.class_id, 
                        func.count(StudentModel.id)).group_by(StudentModel.class_id).all()
    return {
        "total_students": total,
        "by_class": [{"class_id": c, "count": cnt} for c, cnt in by_class]
    }

# ==========================================================
# [3단계] 혼합 라우터 - 일부 정적, 일부 동적
# ==========================================================

# ✅ [SUMMARY] 특정 학생 성적 요약
@router.get("/{student_id}/grade-summary")
def get_student_grade_summary(student_id: int, db: Session = Depends(get_db)):
    grades = db.query(GradeModel).filter(GradeModel.student_id == student_id).all()
    if not grades:
        raise HTTPException(status_code=404, detail="성적 정보가 없습니다")
    avg_score = sum([g.score for g in grades]) / len(grades)
    return {
        "total_subjects": len(grades),
        "average_score": avg_score,
        "grades": [{"subject": g.subject_id, "score": g.score} for g in grades]
    }

# ✅ [SUMMARY] 특정 학생 출결 요약
@router.get("/{student_id}/attendance-summary")
def get_student_attendance_summary(student_id: int, db: Session = Depends(get_db)):
    records = db.query(AttendanceModel).filter(AttendanceModel.student_id == student_id).all()
    if not records:
        raise HTTPException(status_code=404, detail="출결 기록이 없습니다")
    summary = {
        "present": sum(1 for r in records if r.status == "출석"),
        "absent": sum(1 for r in records if r.status == "결석"),
        "late": sum(1 for r in records if r.status == "지각")
    }
    return summary

# ✅ [READ] 특정 학생 상담 기록 조회
@router.get("/{student_id}/meetings")
def get_student_meetings(student_id: int, db: Session = Depends(get_db)):
    meetings = db.query(MeetingModel).filter(MeetingModel.student_id == student_id).all()
    if not meetings:
        raise HTTPException(status_code=404, detail="상담 기록이 없습니다")
    return meetings

# ==========================================================
# [4단계] 완전 동적 라우터 - 맨 마지막에 배치!
# ==========================================================

# ✅ [READ] 특정 학생 상세 조회
@router.get("/{student_id}", response_model=Student)
def read_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="학생 정보를 찾을 수 없습니다")
    return student

# ✅ [UPDATE] 특정 학생 정보 수정
@router.put("/{student_id}", response_model=Student)
def update_student(student_id: int, updated: StudentCreate, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="학생 정보를 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    return student

# ✅ [DELETE] 특정 학생 삭제
@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="학생 정보를 찾을 수 없습니다")
    db.delete(student)
    db.commit()
    return {"message": "✅ 학생 정보가 성공적으로 삭제되었습니다"}
