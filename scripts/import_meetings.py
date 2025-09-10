import csv
from datetime import datetime
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.meetings import Meeting as MeetingModel
from models.students import Student as StudentModel
from models.teachers import Teacher as TeacherModel

# ==========================================================
# [설정] CSV 파일 경로
# ==========================================================
CSV_PATH = "data/meetings.csv"  # ⚠️ 경로 확인 필요


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
                    int(row["student_id"]) if row.get("student_id") and row["student_id"].strip() else None
                )

                # ✅ FK 검증: student_id 존재 여부 확인
                if student_id:
                    exists = db.query(StudentModel).filter_by(id=student_id).first()
                    if not exists:
                        print(f"⚠️ 학생 ID {student_id} 없음 → 건너뜀 (row ID: {row['id']})")
                        continue

                # ✅ teacher_id: 필수 값
                if not row.get("teacher_id") or not row["teacher_id"].strip():
                    print(f"⚠️ 누락된 teacher_id → {row}")
                    continue
                teacher_id = int(row["teacher_id"])

                # ✅ date: YYYY-MM-DD 형식 변환
                meeting_date = None
                if row.get("date") and row["date"].strip():
                    try:
                        meeting_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                    except ValueError:
                        print(f"⚠️ 잘못된 날짜 형식 → {row['date']} (ID: {row['id']})")
                        continue

                # ✅ time: HH:MM 형식 변환
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
                    title=row.get("title"),                # 상담 제목
                    meeting_type=row.get("meeting_type"),  # 상담 유형
                    student_id=student_id,                 # 학생 ID (FK)
                    teacher_id=teacher_id,                 # 교사 ID (FK)
                    date=meeting_date,                     # 상담 날짜
                    time=meeting_time,                     # 상담 시간
                    location=row.get("location"),          # 상담 장소
                )

                db.add(meeting)

            except Exception as e:
                print(f"❌ 오류 발생 (row ID: {row.get('id')}): {e}")
                continue

    db.commit()
    db.close()
    print("✅ 상담 기록 CSV → DB 마이그레이션 완료")


# ==========================================================
# [실행부]
# ==========================================================
if __name__ == "__main__":
    migrate_meetings()
