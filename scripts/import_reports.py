import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.reports import Report as ReportModel  # ✅ 모델 import

CSV_PATH = "data/reports.csv"  # ✅ 파일 경로

def migrate_reports():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            report = ReportModel(
                id=int(row["id"]),                      # 보고서 고유 ID
                student_id=int(row["student_id"]),      # 학생 ID
                date=row["date"],                       # 상담/지도 일자
                type=row["type"],                       # 보고서 유형 (예: 상담, 지도)
                content_raw=row["content_raw"],         # 원본 상담/지도 내용
                summary=row["summary"],                 # 요약된 상담 내용
                emotion=row["emotion"]                  # 감정 태그 (예: 불안, 우울 등)
            )
            db.add(report)

    db.commit()
    db.close()
    print("✅ 보고서 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_reports()
