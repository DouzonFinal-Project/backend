from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.students import Student as StudentModel
from models.grades import Grade as GradeModel
from models.subjects import Subject as SubjectModel

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
# [대시보드] 반 성적 요약
# ==========================================================
@router.get("/dashboard/{class_id}")
def get_grades_dashboard(class_id: int, db: Session = Depends(get_db)):
    # 반 학생 조회
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        return {"success": False, "error": {"code": 404, "message": "데이터 없음"}}

    student_data = []
    all_scores = []
    subject_scores = {}

    for student in students:
        grades = (
            db.query(GradeModel, SubjectModel)
            .join(SubjectModel, SubjectModel.id == GradeModel.subject_id)
            .filter(GradeModel.student_id == student.id)
            .all()
        )

        scores, total_score, subject_count = {}, 0, 0
        for grade, subject in grades:
            # ✅ 성적 알파벳 제거 → 숫자 점수만 기록
            scores[subject.name] = grade.average_score
            if grade.average_score is not None:
                total_score += grade.average_score
                subject_count += 1
                all_scores.append(grade.average_score)

                # 과목별 집계
                if subject.name not in subject_scores:
                    subject_scores[subject.name] = []
                subject_scores[subject.name].append(grade.average_score)

        avg_score = round(total_score / subject_count, 1) if subject_count else 0
        student_data.append({
            "student_id": student.id,
            "name": student.student_name,
            "scores": scores,   # {"국어": 82, "수학": 77, ...}
            "average": avg_score
        })

    # 반 전체 평균
    class_avg = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0

    # 과목별 평균
    subject_avg = {
        subject: round(sum(scores) / len(scores), 1)
        for subject, scores in subject_scores.items()
    }

    # 최저/최고 학생
    best_student = max(student_data, key=lambda x: x["average"]) if student_data else None
    worst_student = min(student_data, key=lambda x: x["average"]) if student_data else None

    # 분포 계산
    distribution = {"0-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0}
    for s in student_data:
        avg = s["average"]
        if avg < 60: distribution["0-59"] += 1
        elif avg < 70: distribution["60-69"] += 1
        elif avg < 80: distribution["70-79"] += 1
        elif avg < 90: distribution["80-89"] += 1
        else: distribution["90-100"] += 1

    # 개별 지도 필요자 (65점 미만)
    below_threshold = [s for s in student_data if s["average"] < 65]

    # ✅ rank 계산 추가
    ranked_students = sorted(student_data, key=lambda x: x["average"], reverse=True)
    for idx, s in enumerate(ranked_students, start=1):
        s["rank"] = idx

    return {
        "success": True,
        "data": {
            "class_id": class_id,
            "overview": {
                "class_avg": class_avg,
                "highest": best_student["average"] if best_student else None,
                "lowest": worst_student["average"] if worst_student else None,
                "need_guidance": len(below_threshold),
            },
            "subject_avg": subject_avg,
            "distribution": distribution,   # ✅ 비율 제거 → 단순 숫자
            "alerts": {
                "below_threshold": below_threshold
            },
            "students": ranked_students      # ✅ rank 포함
        }
    }
