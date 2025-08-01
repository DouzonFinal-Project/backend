import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.test_scores import TestScore as TestScoreModel  # ✅ 모델 import

CSV_PATH = "data/test_scores.csv"  # ✅ 파일 경로

def migrate_test_scores():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            test_score = TestScoreModel(
                id=int(row["id"]),                  # 시험 성적 고유 ID
                test_id=int(row["test_id"]),        # 시험 ID
                student_id=int(row["student_id"]),  # 학생 ID
                score=float(row["score"]),          # 시험 점수
                subject_name=row["subject_name"]    # 과목 이름 (중복 저장)
            )
            db.add(test_score)

    db.commit()
    db.close()
    print("✅ 시험 성적 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_test_scores()
