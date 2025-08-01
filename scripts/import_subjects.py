import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.subjects import Subject as SubjectModel  # ✅ 모델 import

CSV_PATH = "data/subjects.csv"  # ✅ 파일 경로

def migrate_subjects():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            subject = SubjectModel(
                id=int(row["id"]),              # 과목 고유 ID
                name=row["name"],               # 과목 이름 (예: 수학, 영어)
                category=row["category"]        # 과목 분류 (예: 필수, 선택)
            )
            db.add(subject)

    db.commit()
    db.close()
    print("✅ 과목 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_subjects()
