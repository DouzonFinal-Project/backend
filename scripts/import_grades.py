import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.grades import Grade as GradeModel  # ✅ 모델 import

CSV_PATH = "data/grades.csv"  # ✅ 파일 경로

def migrate_grades():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            grade = GradeModel(
                id=int(row["id"]),                          # 성적 고유 ID
                student_id=int(row["student_id"]),          # 학생 ID
                subject_id=int(row["subject_id"]),          # 과목 ID
                term=1 if "1" in row["term"] else 2,                      # 학기
                average_score=float(row["average_score"]),  # 평균 점수
                grade_letter=row["grade_letter"]            # 성적 등급 (예: A, B)
            )
            db.add(grade)

    db.commit()
    db.close()
    print("✅ 성적 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_grades()
