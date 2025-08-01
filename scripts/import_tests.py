import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.tests import Test as TestModel  # ✅ 모델 import

CSV_PATH = "data/tests.csv"  # ✅ 파일 경로

def migrate_tests():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            test = TestModel(
                id=int(row["id"]),                   # 시험 고유 ID
                subject_id=int(row["subject_id"]),   # 과목 ID
                test_name=row["test_name"],          # 시험명
                test_date=row["test_date"],          # 시험 날짜
                class_id=int(row["class_id"]),       # 대상 학급 ID
                subject_name=row["subject_name"]     # 과목 이름 (중복 저장)
            )
            db.add(test)

    db.commit()
    db.close()
    print("✅ 시험 정보 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_tests()
