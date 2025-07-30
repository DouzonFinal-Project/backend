import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.school_report import SchoolReport  # ✅ 모델 임포트

CSV_PATH = "data/school_report.csv"  # 📍 실제 파일 경로 확인

def migrate_school_report():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            record = SchoolReport(
                student_id=int(row["student_id"]),
                student_name=row["student_name"],
                behavior_summary=row["behavior_summary"],
                career_aspiration=row["career_aspiration"],
                teacher_feedback=row["teacher_feedback"]
            )
            db.add(record)

    db.commit()
    db.close()
    print("✅ 학교생활 종합보고서 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_school_report()
