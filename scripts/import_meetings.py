import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.meetings import Meeting as MeetingModel  # ✅ 모델 import

CSV_PATH = "data/meetings.csv"  # ✅ 파일 경로

def migrate_meetings():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                # ✅ student_id는 비어 있으면 None으로 처리
                student_id = (
                    int(float(row["student_id"])) if row["student_id"].strip() else None
                )

                # ✅ teacher_id는 필수
                if not row["teacher_id"].strip():
                    print(f"⚠️ 누락된 teacher_id → {row}")
                    continue
                teacher_id = int(float(row["teacher_id"]))

                meeting = MeetingModel(
                    id=int(row["id"]),                      # 상담 고유 ID
                    title=row["title"],                     # 상담 제목
                    meeting_type=row["meeting_type"],       # 상담 유형 (예: 상담, 회의 등)
                    student_id=student_id,                  # 학생 ID 또는 None (교무회의용)
                    teacher_id=teacher_id                   # 교사 ID
                )
                db.add(meeting)

            except Exception as e:
                print(f"❌ 오류 발생 (ID: {row.get('id')}): {e}")
                continue

    db.commit()
    db.close()
    print("✅ 상담기록 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_meetings()
