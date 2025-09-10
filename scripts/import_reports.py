import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.reports import Report as ReportModel  # ✅ Report 모델
from models.meetings import Meeting as MeetingModel  # ✅ FK 검증용

CSV_PATH = "data/reports.csv"  # ⚠️ 경로 확인


def migrate_reports():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                # ✅ meeting_id 확인
                meeting_id = int(row["meeting_id"])
                meeting = db.query(MeetingModel).filter_by(id=meeting_id).first()
                if not meeting:
                    print(f"⚠️ meeting_id {meeting_id} 없음 → 건너뜀 (row ID: {row['id']})")
                    continue

                # ✅ DB 객체 생성 (date 제거됨)
                report = ReportModel(
                    id=int(row["id"]),
                    meeting_id=meeting_id,
                    type=row.get("report_type"),           # 보고서 유형
                    content_raw=row.get("content_raw"),
                    summary=row.get("summary"),
                    emotion=row.get("emotion"),
                )

                db.add(report)

            except Exception as e:
                print(f"❌ 오류 발생 (row ID: {row.get('id')}): {e}")
                continue

    db.commit()
    db.close()
    print("✅ 보고서 CSV → DB 마이그레이션 완료")


if __name__ == "__main__":
    migrate_reports()
