import csv
from datetime import datetime
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.meetings import Meeting as MeetingModel  # ✅ 모델 import

# ==========================================================
# [설정] CSV 파일 경로
# ==========================================================
CSV_PATH = "data/meetings.csv"  # ✅ meetings.csv 파일 경로


# ==========================================================
# [함수] 상담 기록 CSV → DB 마이그레이션
# ==========================================================
def migrate_meetings():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                # ✅ student_id: 비어 있으면 None 처리
                student_id = (
                    int(float(row["student_id"])) if row["student_id"].strip() else None
                )

                # ✅ teacher_id: 필수 값
                if not row["teacher_id"].strip():
                    print(f"⚠️ 누락된 teacher_id → {row}")
                    continue
                teacher_id = int(float(row["teacher_id"]))

                # ✅ date: YYYY-MM-DD 형식
                meeting_date = None
                if row.get("date") and row["date"].strip():
                    try:
                        meeting_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                    except ValueError:
                        print(f"⚠️ 잘못된 날짜 형식 → {row['date']} (ID: {row['id']})")
                        continue

                # ✅ time: HH:MM 형식
                meeting_time = None
                if row.get("time") and row["time"].strip():
                    try:
                        meeting_time = datetime.strptime(row["time"], "%H:%M").time()
                    except ValueError:
                        print(f"⚠️ 잘못된 시간 형식 → {row['time']} (ID: {row['id']})")
                        continue

                # ✅ DB 객체 생성
                meeting = MeetingModel(
                    id=int(row["id"]),                     # 상담 고유 ID (PK)
                    title=row["title"],                    # 상담 제목
                    meeting_type=row["meeting_type"],      # 상담 유형
                    student_id=student_id,                 # 학생 ID
                    teacher_id=teacher_id,                 # 교사 ID
                    date=meeting_date,                     # 상담 날짜
                    time=meeting_time,                     # 상담 시간
                    location=row["location"],              # 상담 장소
                )

                db.add(meeting)

            except Exception as e:
                print(f"❌ 오류 발생 (ID: {row.get('id')}): {e}")
                continue

    db.commit()
    db.close()
    print("✅ 상담 기록 CSV → DB 마이그레이션 완료")


# ==========================================================
# [실행부] 단독 실행 시 수행
# ==========================================================
if __name__ == "__main__":
    migrate_meetings()
