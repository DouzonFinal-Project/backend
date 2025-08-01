import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.events import Event as EventModel  # ✅ 모델 import

CSV_PATH = "data/events.csv"  # ✅ 파일 경로

def migrate_events():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            event = EventModel(
                id=int(row["id"]),                   # 일정 고유 ID
                event_name=row["event_name"],        # 행사/일정 이름
                event_type=row["event_type"],        # 일정 유형 (예: 공휴일, 행사 등)
                date=row["date"],                    # 날짜
                description=row["description"]       # 상세 설명
            )
            db.add(event)

    db.commit()
    db.close()
    print("✅ 학사일정 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_events()
