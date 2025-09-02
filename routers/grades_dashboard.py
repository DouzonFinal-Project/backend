from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.db import SessionLocal
from models.students import Student as StudentModel
from models.grades import Grade as GradeModel
from datetime import datetime

router = APIRouter(prefix="/grades/dashboard", tags=["성적 대시보드"])

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
# [READ] 성적 대시보드 (반 단위)
# ==========================================================
@router.get("/{class_id}")
def get_grades_dashboard(class_id: int, db: Session = Depends(get_db)):
    """
    특정 반(class_id)의 성적 대시보드 데이터 조회
    - 반 평균 / 최고 / 최저
    - 과목별 평균
    - 성적 분포 (구간별 인원수)
    - 학생별 성적표 + 평균 + 석차
    - 65점 미만 지도 필요 학생
    """

    # ✅ 반 학생 목록
    students = db.query(StudentModel).filter(StudentModel.class_id == class_id).all()
    if not students:
        return {
            "success": False,
            "error": {"code": 404, "message": "해당 반에 학생이 없습니다"}
        }

    student_ids = [s.id for s in students]

    # ✅ 전체 성적 불러오기
    grades = (
        db.query(GradeModel)
        .filter(GradeModel.student_id.in_(student_ids))
        .all()
    )
    if not grades:
        return {
            "success": False,
            "error": {"code": 404, "message": "성적 데이터가 없습니다"}
        }

    # ✅ 학생별 성적 집계
    student_scores = {}
    for g in grades:
        if g.student_id not in student_scores:
            student_scores[g.student_id] = {"scores": {}, "total": 0, "count": 0}
        student_scores[g.student_id]["scores"][g.subject_name] = g.score
        student_scores[g.student_id]["total"] += g.score
        student_scores[g.student_id]["count"] += 1

    # ✅ 개인 평균 및 석차
    student_avgs = []
    for sid, data in student_scores.items():
        avg = data["total"] / data["count"] if data["count"] else 0
        student_avgs.append((sid, avg))
    student_avgs.sort(key=lambda x: x[1], reverse=True)
    ranks = {sid: i+1 for i, (sid, _) in enumerate(student_avgs)}

    # ✅ 반 평균 / 최고 / 최저
    all_scores = [g.score for g in grades]
    class_avg = round(sum(all_scores) / len(all_scores), 1)
    highest = max(all_scores)
    lowest = min(all_scores)

    # ✅ 과목별 평균
    subject_avg_query = (
        db.query(
            GradeModel.subject_name,
            func.avg(GradeModel.score).label("avg_score")
        )
        .filter(GradeModel.student_id.in_(student_ids))
        .group_by(GradeModel.subject_name)
        .all()
    )
    subject_avg = {row.subject_name: round(row.avg_score, 1) for row in subject_avg_query}

    # ✅ 성적 분포
    distribution = {"90+": 0, "80-89": 0, "70-79": 0, "60-69": 0, "<60": 0}
    for _, avg in student_avgs:
        if avg >= 90: distribution["90+"] += 1
        elif avg >= 80: distribution["80-89"] += 1
        elif avg >= 70: distribution["70-79"] += 1
        elif avg >= 60: distribution["60-69"] += 1
        else: distribution["<60"] += 1

    # ✅ 학생별 성적표
    students_data = []
    for sid, avg in student_avgs:
        s = next((st for st in students if st.id == sid), None)
        if not s:
            continue
        students_data.append({
            "id": s.id,
            "student_name": s.student_name,
            "scores": student_scores[sid]["scores"],
            "avg": round(avg, 1),
            "rank": ranks[sid]
        })

    # ✅ 지도 필요한 학생 (65점 미만)
    below_students = [s for s in students_data if s["avg"] < 65]

    # ✅ 최종 응답
    return {
        "success": True,
        "data": {
            "class_id": class_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "overview": {
                "class_avg": class_avg,
                "highest": highest,
                "lowest": lowest,
                "total_students": len(students)
            },
            "subject_avg": subject_avg,
            "distribution": distribution,
            "students": students_data,
            "alerts": {
                "need_guidance": len(below_students),
                "below_threshold": [
                    {"name": s["student_name"], "avg": s["avg"]} for s in below_students
                ]
            }
        },
        "message": f"{class_id}반 성적 대시보드 조회 성공"
    }
