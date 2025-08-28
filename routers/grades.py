from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.db import SessionLocal
from models.grades import Grade as GradeModel
from schemas.grades import Grade as GradeSchema

# 추가 모델 import
from models.students import Student as StudentModel
from models.subjects import Subject as SubjectModel
from models.classes import Class as ClassModel

router = APIRouter(prefix="/grades", tags=["grades"])

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
# [1단계] 정적 분석/요약 라우터
# ==========================================================

# ✅ [PIVOT] 반(class_id) 기준 학생별 성적 피벗
# - 한 반 학생들의 과목별 점수와 개인 평균 제공
@router.get("/pivot")
def get_class_grades(class_id: int, db: Session = Depends(get_db)):
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        return {"success": False, "error": {"code": 404, "message": "No students found for this class"}}

    result = []
    for student in students:
        grades = db.query(GradeModel).filter(GradeModel.student_id == student.id).all()
        scores, total_score, subject_count = {}, 0, 0

        for grade in grades:
            subject = db.query(SubjectModel).filter(SubjectModel.id == grade.subject_id).first()
            if subject:
                scores[subject.name] = {
                    "average_score": grade.average_score,
                    "grade_letter": grade.grade_letter
                }
                if grade.average_score is not None:
                    total_score += grade.average_score
                    subject_count += 1

        avg_score = round(total_score / subject_count, 1) if subject_count else 0
        class_obj = db.query(ClassModel).filter(ClassModel.id == student.class_id).first()
        class_name = f"{class_obj.grade}-{class_obj.class_num}" if class_obj else "Unknown"

        result.append({
            "student_id": student.id,
            "name": student.student_name,
            "class": class_name,
            "scores": scores,
            "average": avg_score
        })

    return {"success": True, "data": result}

# ✅ [RANKING] 반 내 평균 점수 기준 등수
@router.get("/rankings")
def get_class_rankings(class_id: int, db: Session = Depends(get_db)):
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        return {"success": False, "error": {"code": 404, "message": "No students found for this class"}}

    results = []
    for student in students:
        grades = db.query(GradeModel).filter(GradeModel.student_id == student.id).all()
        avg_score = round(sum([g.average_score for g in grades if g.average_score is not None]) / len(grades), 1) if grades else 0.0
        results.append({
            "student_id": student.id,
            "name": student.student_name,
            "avg_score": avg_score,
            "grade_letters": [g.grade_letter for g in grades if g.grade_letter]
        })

    sorted_results = sorted(results, key=lambda x: x["avg_score"], reverse=True)
    for idx, item in enumerate(sorted_results, start=1):
        item["rank"] = idx

    return {"success": True, "data": sorted_results}

# ✅ [SUMMARY] 반 전체 평균 점수
@router.get("/summary")
def get_class_average_score(class_id: int, db: Session = Depends(get_db)):
    student_ids = db.query(StudentModel.id).filter(StudentModel.class_id == class_id).all()
    student_ids = [s[0] for s in student_ids]

    if not student_ids:
        return {"success": False, "error": {"code": 404, "message": "No students found for this class"}}

    avg_result = (
        db.query(func.avg(GradeModel.average_score))
        .filter(GradeModel.student_id.in_(student_ids))
        .scalar()
    )
    avg_score = round(avg_result, 1) if avg_result else 0.0

    return {"success": True, "data": {"class_id": class_id, "average_score": avg_score}}

# ✅ [DISTRIBUTION] 점수 구간별 학생 수 분포
@router.get("/distribution")
def get_score_distribution(class_id: int, db: Session = Depends(get_db)):
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        return {"success": False, "error": {"code": 404, "message": "No students found for this class"}}

    distribution = {"0~59": 0, "60~69": 0, "70~79": 0, "80~89": 0, "90~100": 0}

    for student in students:
        grades = db.query(GradeModel).filter(GradeModel.student_id == student.id).all()
        if not grades:
            continue
        avg_score = sum([g.average_score for g in grades if g.average_score is not None]) / len(grades)
        if avg_score < 60: distribution["0~59"] += 1
        elif avg_score < 70: distribution["60~69"] += 1
        elif avg_score < 80: distribution["70~79"] += 1
        elif avg_score < 90: distribution["80~89"] += 1
        else: distribution["90~100"] += 1

    return {"success": True, "data": {"class_id": class_id, "distribution": distribution}}

# ✅ [LOW PERFORMERS] 기준 미달 학생 목록
@router.get("/low-performers")
def get_low_performers(class_id: int, threshold: float = 65.0, db: Session = Depends(get_db)):
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        return {"success": False, "error": {"code": 404, "message": "No students found for this class"}}

    low_performers = []
    for student in students:
        grades = db.query(GradeModel).filter(GradeModel.student_id == student.id).all()
        if not grades:
            continue
        avg_score = sum([g.average_score for g in grades if g.average_score is not None]) / len(grades)
        if avg_score < threshold:
            low_performers.append({
                "student_id": student.id,
                "name": student.student_name,
                "average": round(avg_score, 1),
                "grade_letters": [g.grade_letter for g in grades if g.grade_letter]
            })

    return {
        "success": True,
        "data": {"class_id": class_id, "threshold": threshold, "count": len(low_performers), "students": low_performers}
    }

# ==========================================================
# [2단계] 부분 동적 라우터 (학생 단위 조회)
# ==========================================================

# ✅ [READ] 특정 학생의 성적 피벗
@router.get("/student/{student_id}")
def get_student_grades(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not student:
        return {"success": False, "error": {"code": 404, "message": "Student not found"}}

    results = (
        db.query(
            SubjectModel.name.label("subject_name"),
            GradeModel.average_score,
            GradeModel.grade_letter
        )
        .join(SubjectModel, SubjectModel.id == GradeModel.subject_id)
        .filter(GradeModel.student_id == student_id)
        .all()
    )
    if not results:
        return {"success": False, "error": {"code": 404, "message": "No grades found for student"}}

    scores = {r.subject_name: {"average_score": r.average_score, "grade_letter": r.grade_letter} for r in results}
    avg_score = round(sum([r.average_score for r in results if r.average_score is not None]) / len(results), 1)

    class_info = db.query(ClassModel).filter(ClassModel.id == student.class_id).first()
    class_name = f"{class_info.grade}-{class_info.class_num}" if class_info else "Unknown"

    return {
        "success": True,
        "data": {
            "student_id": student.id,
            "name": student.student_name,
            "class": class_name,
            "scores": scores,
            "average": avg_score
        }
    }

# ==========================================================
# [3단계] CRUD 기본 라우터
# ==========================================================

# ✅ [CREATE] 성적 추가
@router.post("/")
def create_grade(grade: GradeSchema, db: Session = Depends(get_db)):
    db_grade = GradeModel(**grade.model_dump())
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return {
        "success": True,
        "data": {
            "id": db_grade.id,
            "student_id": db_grade.student_id,
            "subject_id": db_grade.subject_id,
            "average_score": db_grade.average_score,
            "grade_letter": db_grade.grade_letter,
            "message": "Grade created successfully"
        }
    }

# ✅ [READ] 전체 성적 조회
@router.get("/")
def read_grades(db: Session = Depends(get_db)):
    records = db.query(GradeModel).all()
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "student_id": r.student_id,
                "subject_id": r.subject_id,
                "average_score": r.average_score,
                "grade_letter": r.grade_letter
            }
            for r in records
        ]
    }

# ==========================================================
# [4단계] 완전 동적 라우터
# ==========================================================

# ✅ [READ] 특정 성적 조회
@router.get("/{grade_id}")
def read_grade(grade_id: int, db: Session = Depends(get_db)):
    grade = db.query(GradeModel).filter(GradeModel.id == grade_id).first()
    if grade is None:
        return {"success": False, "error": {"code": 404, "message": "Grade not found"}}
    return {
        "success": True,
        "data": {
            "id": grade.id,
            "student_id": grade.student_id,
            "subject_id": grade.subject_id,
            "average_score": grade.average_score,
            "grade_letter": grade.grade_letter
        }
    }

# ✅ [UPDATE] 성적 수정
@router.put("/{grade_id}")
def update_grade(grade_id: int, updated: GradeSchema, db: Session = Depends(get_db)):
    grade = db.query(GradeModel).filter(GradeModel.id == grade_id).first()
    if grade is None:
        return {"success": False, "error": {"code": 404, "message": "Grade not found"}}

    for key, value in updated.model_dump().items():
        setattr(grade, key, value)

    db.commit()
    db.refresh(grade)
    return {
        "success": True,
        "data": {
            "id": grade.id,
            "student_id": grade.student_id,
            "subject_id": grade.subject_id,
            "average_score": grade.average_score,
            "grade_letter": grade.grade_letter,
            "message": "Grade updated successfully"
        }
    }

# ✅ [DELETE] 성적 삭제
@router.delete("/{grade_id}")
def delete_grade(grade_id: int, db: Session = Depends(get_db)):
    grade = db.query(GradeModel).filter(GradeModel.id == grade_id).first()
    if grade is None:
        return {"success": False, "error": {"code": 404, "message": "Grade not found"}}

    db.delete(grade)
    db.commit()
    return {
        "success": True,
        "data": {"grade_id": grade_id, "message": "Grade deleted successfully"}
    }
