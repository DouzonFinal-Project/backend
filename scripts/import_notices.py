import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.notices import Notice as NoticeModel  # ✅ 모델 import

CSV_PATH = "data/notices.csv"  # ✅ 파일 경로

def migrate_notices():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            notice = NoticeModel(
                id=int(row["id"]),                           # 공지 고유 ID
                title=row["title"],                          # 공지 제목
                content=row["content"],                      # 공지 내용
                target_class_id=int(row["target_class_id"]), # 대상 학급 ID
                date=row["date"],                            # 작성일자
                is_important=bool(int(row["is_important"]))  # ✅ 중요 여부 (0/1 → False/True)
            )
            db.add(notice)

    db.commit()
    db.close()
    print("✅ 공지사항 CSV → DB 마이그레이션 완료 (is_important 포함)")

if __name__ == "__main__":
    migrate_notices()
