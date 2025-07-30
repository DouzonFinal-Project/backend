import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.grades import Grade  # ✅ 모델 임포트

CSV_PATH = "data/grades.csv"  # ✅ CSV 파일 경로

def migrate_grades():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # CSV 필드와 모델 필드 매핑
            record = Grade(
                student_id=int(row["student_id"]),
                student_name=row["student_name"],
                subject=row["subject"],
                test_score=float(row["test_score"]),
                assignment_score=float(row["assignment_score"]),
                total_score=float(row["total_score"])
            )
            db.add(record)

    db.commit()
    db.close()
    print("✅ 성적 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_grades()
