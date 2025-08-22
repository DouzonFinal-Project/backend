from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.db import SessionLocal
from models.classes import Class as ClassModel
from models.students import Student as StudentModel
from models.teachers import Teacher as TeacherModel
from models.grades import Grade as GradeModel
from models.attendance import Attendance as AttendanceModel
from schemas.classes import Class, ClassCreate

router = APIRouter(prefix="/classes", tags=["학급 정보"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================================
# [1단계] CRUD 기본 라우터 - 루트 경로 우선 처리
# ==========================================================

# ✅ [CREATE] 학급 추가
@router.post("/", response_model=Class)
def create_class(new_class: ClassCreate, db: Session = Depends(get_db)):
    db_class = ClassModel(**new_class.model_dump())
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

# ✅ [READ] 전체 학급 조회
@router.get("/", response_model=list[Class])
def read_classes(db: Session = Depends(get_db)):
    return db.query(ClassModel).all()

# ==========================================================
# [2단계] 정적 라우터 - 구체적인 경로들
# ==========================================================

# ✅ [READ] 학급별 학생 목록 조회
@router.get("/{class_id}/students", response_model=list[dict])
def get_class_students(class_id: int, db: Session = Depends(get_db)):
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        raise HTTPException(status_code=404, detail="해당 반에 학생이 없습니다")
    return [{"id": s.id, "student_no": s.student_no, "name": s.student_name} for s in students]

# ✅ [READ] 학급별 교사 목록 조회
@router.get("/{class_id}/teachers", response_model=list[dict])
def get_class_teachers(class_id: int, db: Session = Depends(get_db)):
    # 담임 + 과목 담당 교사 조회
    teachers = db.query(TeacherModel).filter(TeacherModel.class_id == class_id).all()
    if not teachers:
        raise HTTPException(status_code=404, detail="해당 반에 교사 정보가 없습니다")
    return [{"id": t.id, "name": t.teacher_name, "subject": t.subject_id} for t in teachers]

# ✅ [SUMMARY] 학급별 학생 수, 평균 성적, 출결 요약
@router.get("/{class_id}/summary")
def get_class_summary(class_id: int, db: Session = Depends(get_db)):
    student_count = db.query(StudentModel).filter(StudentModel.class_id == class_id).count()
    avg_score = db.query(func.avg(GradeModel.score)).join(StudentModel, GradeModel.student_id == StudentModel.id)\
        .filter(StudentModel.class_id == class_id).scalar()
    attendance_summary = db.query(
        AttendanceModel.status, func.count(AttendanceModel.id)
    ).join(StudentModel, AttendanceModel.student_id == StudentModel.id)\
        .filter(StudentModel.class_id == class_id).group_by(AttendanceModel.status).all()

    return {
        "student_count": student_count,
        "average_score": avg_score,
        "attendance": {status: cnt for status, cnt in attendance_summary}
    }

# ✅ [SUMMARY] 전체 학급 요약 (반별 학생 수, 평균 성적)
@router.get("/summary")
def classes_summary(db: Session = Depends(get_db)):
    class_stats = db.query(
        ClassModel.id,
        ClassModel.class_name,
        func.count(StudentModel.id).label("student_count"),
        func.avg(GradeModel.score).label("avg_score")
    ).outerjoin(StudentModel, StudentModel.class_id == ClassModel.id)\
     .outerjoin(GradeModel, GradeModel.student_id == StudentModel.id)\
     .group_by(ClassModel.id, ClassModel.class_name).all()

    return [
        {"class_id": cid, "class_name": cname, "student_count": sc, "average_score": avg}
        for cid, cname, sc, avg in class_stats
    ]

# ==========================================================
# [3단계] 혼합 라우터 - (필요시 확장 가능)
# ==========================================================
# 예: /classes/{class_id}/report 같은 혼합형 라우터는 필요시 구현

# ==========================================================
# [4단계] 완전 동적 라우터 - 맨 마지막에 배치!
# ==========================================================

# ✅ [READ] 특정 학급 조회
@router.get("/{class_id}", response_model=Class)
def read_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if cls is None:
        raise HTTPException(status_code=404, detail="학급 정보를 찾을 수 없습니다")
    return cls

# ✅ [UPDATE] 학급 정보 수정
@router.put("/{class_id}", response_model=Class)
def update_class(class_id: int, updated: ClassCreate, db: Session = Depends(get_db)):
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if cls is None:
        raise HTTPException(status_code=404, detail="학급 정보를 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(cls, key, value)
    db.commit()
    db.refresh(cls)
    return cls

# ✅ [DELETE] 학급 삭제
@router.delete("/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if cls is None:
        raise HTTPException(status_code=404, detail="학급 정보를 찾을 수 없습니다")
    db.delete(cls)
    db.commit()
    return {"message": "✅ 학급 정보가 성공적으로 삭제되었습니다"}
