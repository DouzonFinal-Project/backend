from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.db import SessionLocal
from models.classes import Class as ClassModel
from models.students import Student as StudentModel
from models.teachers import Teacher as TeacherModel
from models.grades import Grade as GradeModel
from models.attendance import Attendance as AttendanceModel
from schemas.classes import Class, ClassCreate

router = APIRouter(prefix="/classes", tags=["classes"])

# ==========================================================
# [공통] DB 세션 관리
# - 모든 요청에서 DB 연결을 생성하고 종료
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

# ✅ [CREATE] 학급 추가
# - 새로운 학급을 생성할 때 사용
# - 예: 3학년 2반을 새로 등록
@router.post("/")
def create_class(new_class: ClassCreate, db: Session = Depends(get_db)):
    db_class = ClassModel(**new_class.model_dump())
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return {
        "success": True,
        "data": {
            "id": db_class.id,
            "grade": db_class.grade,
            "class_num": db_class.class_num,
            "teacher_id": db_class.teacher_id,
            "message": "Class created successfully"
        }
    }

# ✅ [READ] 전체 학급 조회
# - 모든 학급 정보를 조회
# - 학교 전체 학급 현황 확인 시 사용
@router.get("/")
def read_classes(db: Session = Depends(get_db)):
    records = db.query(ClassModel).all()
    return {
        "success": True,
        "data": [
            {"id": r.id, "grade": r.grade, "class_num": r.class_num, "teacher_id": r.teacher_id}
            for r in records
        ]
    }

# ==========================================================
# [2단계] 정적 라우터
# ==========================================================

# ✅ [READ] 학급별 학생 목록 조회
# - 특정 학급에 속한 학생들의 기본 정보 확인
@router.get("/{class_id}/students")
def get_class_students(class_id: int, db: Session = Depends(get_db)):
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        return {"success": False, "error": {"code": 404, "message": "No students found for this class"}}
    return {
        "success": True,
        "data": [
            {"id": s.id, "name": s.student_name, "gender": s.gender, "phone": s.phone}
            for s in students
        ]
    }

# ✅ [READ] 학급별 교사 목록 조회
# - 특정 학급을 담당하는 교사 정보 조회
@router.get("/{class_id}/teachers")
def get_class_teachers(class_id: int, db: Session = Depends(get_db)):
    teachers = db.query(TeacherModel).filter(TeacherModel.class_id == class_id).all()
    if not teachers:
        return {"success": False, "error": {"code": 404, "message": "No teachers found for this class"}}
    return {
        "success": True,
        "data": [
            {"id": t.id, "name": t.name, "subject": t.subject, "role": t.role}
            for t in teachers
        ]
    }

# ✅ [SUMMARY] 학급별 요약 (학생 수, 평균 성적, 출결 통계)
# - 한 반의 전반적인 상태를 요약해서 제공
@router.get("/{class_id}/summary")
def get_class_summary(class_id: int, db: Session = Depends(get_db)):
    # 학생 수
    student_count = db.query(StudentModel).filter(StudentModel.class_id == class_id).count()

    # 평균 성적
    avg_score = db.query(func.avg(GradeModel.average_score)) \
        .join(StudentModel, GradeModel.student_id == StudentModel.id) \
        .filter(StudentModel.class_id == class_id).scalar()

    # 출결 요약
    attendance_summary = db.query(
        AttendanceModel.status, func.count(AttendanceModel.id)
    ).join(StudentModel, AttendanceModel.student_id == StudentModel.id) \
     .filter(StudentModel.class_id == class_id) \
     .group_by(AttendanceModel.status).all()

    return {
        "success": True,
        "data": {
            "class_id": class_id,
            "student_count": student_count,
            "average_score": avg_score,
            "attendance": {status: cnt for status, cnt in attendance_summary}
        }
    }

# ✅ [SUMMARY] 전체 학급 요약
# - 전 학급 단위의 학생 수, 평균 성적 현황
@router.get("/summary")
def classes_summary(db: Session = Depends(get_db)):
    class_stats = db.query(
        ClassModel.id,
        func.count(StudentModel.id).label("student_count"),
        func.avg(GradeModel.average_score).label("avg_score")
    ).outerjoin(StudentModel, StudentModel.class_id == ClassModel.id) \
     .outerjoin(GradeModel, GradeModel.student_id == StudentModel.id) \
     .group_by(ClassModel.id).all()

    return {
        "success": True,
        "data": [
            {"class_id": cid, "student_count": sc, "average_score": avg}
            for cid, sc, avg in class_stats
        ]
    }

# ==========================================================
# [3단계] 혼합 라우터 (추후 확장 가능)
# ==========================================================
# 예: /classes/{class_id}/report 같은 라우터 확장 가능

# ==========================================================
# [4단계] 동적 라우터
# ==========================================================

# ✅ [READ] 특정 학급 조회
# - 학급 ID로 단일 학급 정보 조회
@router.get("/{class_id}")
def read_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if cls is None:
        return {"success": False, "error": {"code": 404, "message": "Class not found"}}
    return {
        "success": True,
        "data": {
            "id": cls.id,
            "grade": cls.grade,
            "class_num": cls.class_num,
            "teacher_id": cls.teacher_id
        }
    }

# ✅ [UPDATE] 학급 정보 수정
# - 학급 번호, 학년, 담당 교사 등을 변경
@router.put("/{class_id}")
def update_class(class_id: int, updated: ClassCreate, db: Session = Depends(get_db)):
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if cls is None:
        return {"success": False, "error": {"code": 404, "message": "Class not found"}}

    for key, value in updated.model_dump().items():
        setattr(cls, key, value)

    db.commit()
    db.refresh(cls)
    return {
        "success": True,
        "data": {
            "id": cls.id,
            "grade": cls.grade,
            "class_num": cls.class_num,
            "teacher_id": cls.teacher_id,
            "message": "Class updated successfully"
        }
    }

# ✅ [DELETE] 학급 삭제
# - 특정 학급 데이터를 완전히 제거
@router.delete("/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if cls is None:
        return {"success": False, "error": {"code": 404, "message": "Class not found"}}

    db.delete(cls)
    db.commit()
    return {
        "success": True,
        "data": {
            "class_id": class_id,
            "message": "Class deleted successfully"
        }
    }
