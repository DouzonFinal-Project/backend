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
                event_id=int(row["event_id"]),       # 이벤트 ID
                title=row["title"],                  # 행사 제목
                date=row["date"],                    # 날짜
                location=row["location"],            # 장소
                target=row["target"]                 # 대상
            )
            db.add(event)

    db.commit()
    db.close()
    print("✅ 학사 일정 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_events()
