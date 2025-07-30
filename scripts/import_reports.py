import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.reports import Report

CSV_PATH = "data/reports.csv"  # 보고서 CSV 경로

def migrate_reports():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            record = Report(
                student_id=int(row["student_id"]),
                student_name=row["student_name"],
                date=row["date"],
                type=row["type"],
                teacher_note=row["teacher_note"]
            )
            db.add(record)

    db.commit()
    db.close()
    print("✅ 상담 보고서 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_reports()
