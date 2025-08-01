import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.school_report import SchoolReport as SchoolReportModel  # ✅ 모델 import

CSV_PATH = "data/school_report.csv"  # ✅ 파일 경로

def migrate_school_report():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            school_report = SchoolReportModel(
                id=int(row["id"]),                          # 고유 ID
                year=int(row["year"]),                      # 연도
                semester=int(row["semester"]),              # 학기
                student_id=int(row["student_id"]),          # 학생 ID
                behavior_summary=row["behavior_summary"],   # 행동 특성 요약
                peer_relation=row["peer_relation"],         # 또래 관계
                career_aspiration=row["career_aspiration"], # 진로 희망
                teacher_feedback=row["teacher_feedback"]    # 종합 의견 (담임)
            )
            db.add(school_report)

    db.commit()
    db.close()
    print("✅ 생활기록부 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_school_report()
