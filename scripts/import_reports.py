import csv
from datetime import datetime
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.reports import Report as ReportModel  # ✅ Report 모델
from models.meetings import Meeting as MeetingModel  # ✅ FK 검증 + 날짜 fallback 용

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

                # ✅ date: CSV 값 우선, 없으면 meeting.date 사용
                report_date = None
                if row.get("date") and row["date"].strip():
                    try:
                        report_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                    except ValueError:
                        print(f"⚠️ 잘못된 날짜 형식 → {row['date']} (ID: {row['id']})")
                        continue
                else:
                    report_date = meeting.date  # fallback

                # ✅ DB 객체 생성
                report = ReportModel(
                    id=int(row["id"]),
                    meeting_id=meeting_id,
                    date=report_date,
                    type=row.get("report_type"),
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
