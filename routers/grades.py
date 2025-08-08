from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.db import SessionLocal
from models.grades import Grade as GradeModel
from schemas.grades import Grade as GradeSchema

# 추가로 필요한 모델 import
from models.students import Student as StudentModel
from models.tests import Test as TestModel
from models.subjects import Subject as SubjectModel
from models.classes import Class as ClassModel

router = APIRouter(prefix="/grades", tags=["성적 정보"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ [PIVOT] 반(class_id) 기준으로 학생별 성적 피벗 출력
@router.get("/pivot")
def get_class_grades(class_id: int, db: Session = Depends(get_db)):
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        raise HTTPException(status_code=404, detail="해당 반에 속한 학생이 없습니다.")

    result = []
    for student in students:
        grades = db.query(GradeModel).filter(GradeModel.student_id == student.id).all()

        scores = {}
        total_score = 0
        subject_count = 0
        for grade in grades:
            subject = db.query(SubjectModel).filter(SubjectModel.id == grade.subject_id).first()
            if subject:
                scores[subject.name] = grade.average_score
                total_score += grade.average_score
                subject_count += 1

        avg_score = round(total_score / subject_count, 1) if subject_count else 0

        class_obj = db.query(ClassModel).get(student.class_id)
        class_name = f"{class_obj.grade}학년 {class_obj.class_num}반" if class_obj else "학급 정보 없음"

        result.append({
            "student_id": student.id,
            "name": student.student_name,
            "class": class_name,
            "scores": scores,
            "개인평균": avg_score
        })

    return result


# ✅ [READ] 특정 학생의 성적 피벗 조회
@router.get("/student/{student_id}")
def get_student_grades(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")

    results = (
        db.query(
            SubjectModel.name.label("subject_name"),
            GradeModel.average_score
        )
        .join(SubjectModel, SubjectModel.id == GradeModel.subject_id)
        .filter(GradeModel.student_id == student_id)
        .all()
    )

    if not results:
        raise HTTPException(status_code=404, detail="해당 학생의 성적이 없습니다.")

    scores = {r.subject_name: r.average_score for r in results}
    avg_score = round(sum(scores.values()) / len(scores), 1)

    class_info = db.query(ClassModel).filter(ClassModel.id == student.class_id).first()
    class_name = f"{class_info.grade}학년 {class_info.class_num}반" if class_info else "학급 정보 없음"

    return {
        "student_id": student.id,
        "name": student.student_name,
        "class": class_name,
        "scores": scores,
        "개인평균": avg_score
    }


# ✅ [RANKING] 반 내 평균 점수 기준 성적 등수 조회
@router.get("/rankings")
def get_class_rankings(class_id: int, db: Session = Depends(get_db)):
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        raise HTTPException(status_code=404, detail="해당 반의 학생 정보를 찾을 수 없습니다.")

    results = []
    for student in students:
        grades = db.query(GradeModel).filter(GradeModel.student_id == student.id).all()
        if grades:
            avg_score = round(sum([g.average_score for g in grades]) / len(grades), 1)
        else:
            avg_score = 0.0

        results.append({
            "student_id": student.id,
            "name": student.student_name,
            "avg_score": avg_score
        })

    sorted_results = sorted(results, key=lambda x: x["avg_score"], reverse=True)

    for idx, item in enumerate(sorted_results, start=1):
        item["rank"] = idx

    return sorted_results


# ✅ [SUMMARY] 반 전체 평균 점수
@router.get("/summary")
def get_class_average_score(class_id: int, db: Session = Depends(get_db)):
    # 반 학생 ID 리스트 가져오기
    student_ids = db.query(StudentModel.id).filter(StudentModel.class_id == class_id).all()
    student_ids = [s[0] for s in student_ids]

    if not student_ids:
        raise HTTPException(status_code=404, detail="해당 반에 학생이 없습니다.")

    # 해당 학생들의 모든 성적 점수 평균 계산
    avg_result = (
        db.query(func.avg(GradeModel.average_score))
        .filter(GradeModel.student_id.in_(student_ids))
        .scalar()
    )

    avg_score = round(avg_result, 1) if avg_result else 0.0

    return {
        "class_id": class_id,
        "average_score": avg_score
    }

# ✅ [DISTRIBUTION] 반(class_id) 기준 점수 구간별 학생 수
@router.get("/distribution")
def get_score_distribution(class_id: int, db: Session = Depends(get_db)):
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        raise HTTPException(status_code=404, detail="해당 반의 학생 정보를 찾을 수 없습니다.")

    # 점수 구간 초기화
    distribution = {
        "0~59": 0,
        "60~69": 0,
        "70~79": 0,
        "80~89": 0,
        "90~100": 0
    }

    for student in students:
        grades = db.query(GradeModel).filter(GradeModel.student_id == student.id).all()
        if not grades:
            continue

        avg_score = sum([g.average_score for g in grades]) / len(grades)

        # 구간 분류
        if avg_score < 60:
            distribution["0~59"] += 1
        elif avg_score < 70:
            distribution["60~69"] += 1
        elif avg_score < 80:
            distribution["70~79"] += 1
        elif avg_score < 90:
            distribution["80~89"] += 1
        else:
            distribution["90~100"] += 1

    return {
        "class_id": class_id,
        "distribution": distribution
    }


# ✅ [LOW PERFORMERS] 평균 점수 기준 미달 학생 목록
@router.get("/low-performers")
def get_low_performers(class_id: int, threshold: float = 65.0, db: Session = Depends(get_db)):
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        raise HTTPException(status_code=404, detail="해당 반의 학생 정보를 찾을 수 없습니다.")

    low_performers = []

    for student in students:
        grades = db.query(GradeModel).filter(GradeModel.student_id == student.id).all()
        if not grades:
            continue

        avg_score = sum([g.average_score for g in grades]) / len(grades)

        if avg_score < threshold:
            low_performers.append({
                "student_id": student.id,
                "name": student.student_name,
                "average": round(avg_score, 1)
            })

    return {
        "class_id": class_id,
        "threshold": threshold,
        "count": len(low_performers),
        "students": low_performers
    }


# ✅ [CREATE] 성적 정보 추가
@router.post("/", response_model=GradeSchema)
def create_grade(grade: GradeSchema, db: Session = Depends(get_db)):
    db_grade = GradeModel(**grade.model_dump())
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade


# ✅ [READ] 전체 성적 조회
@router.get("/", response_model=list[GradeSchema])
def read_grades(db: Session = Depends(get_db)):
    return db.query(GradeModel).all()


# ✅ [READ] 특정 성적 조회
@router.get("/{grade_id}", response_model=GradeSchema)
def read_grade(grade_id: int, db: Session = Depends(get_db)):
    grade = db.query(GradeModel).filter(GradeModel.id == grade_id).first()
    if grade is None:
        raise HTTPException(status_code=404, detail="성적 정보를 찾을 수 없습니다")
    return grade


# ✅ [UPDATE] 성적 정보 수정
@router.put("/{grade_id}", response_model=GradeSchema)
def update_grade(grade_id: int, updated: GradeSchema, db: Session = Depends(get_db)):
    grade = db.query(GradeModel).filter(GradeModel.id == grade_id).first()
    if grade is None:
        raise HTTPException(status_code=404, detail="성적 정보를 찾을 수 없습니다")
    for key, value in updated.model_dump().items():
        setattr(grade, key, value)
    db.commit()
    db.refresh(grade)
    return grade


# ✅ [DELETE] 성적 삭제
@router.delete("/{grade_id}")
def delete_grade(grade_id: int, db: Session = Depends(get_db)):
    grade = db.query(GradeModel).filter(GradeModel.id == grade_id).first()
    if grade is None:
        raise HTTPException(status_code=404, detail="성적 정보를 찾을 수 없습니다")
    db.delete(grade)
    db.commit()
    return {"message": "성적 정보가 성공적으로 삭제되었습니다"}
