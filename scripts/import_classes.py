import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.classes import Class as ClassModel  # ✅ 모델 import

CSV_PATH = "data/classes.csv"  # ✅ 파일 경로

def migrate_classes():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            class_record = ClassModel(
                id=int(row["id"]),                   # 학급 고유 ID (Primary Key)
                grade=int(row["grade"]),             # 학년
                class_num=int(row["class_num"]),     # 반 번호
                teacher_id=int(row["teacher_id"])    # 담임 교사 ID
            )
            db.add(class_record)

    db.commit()
    db.close()
    print("✅ 학급 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_classes()
