import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.attendance import Attendance as AttendanceModel  # ✅ 모델 import

CSV_PATH = "data/attendance.csv"  # ✅ 파일 경로

def migrate_attendance():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            attendance = AttendanceModel(
                id=int(row["id"]),                   # 출결 ID (Primary Key)
                student_id=int(row["student_id"]),   # 학생 ID
                date=row["date"],                    # 날짜
                status=row["status"],                # 출결 상태 (예: 출석, 결석, 지각)
                reason=row["reason"],                # 사유 (결석/조퇴 등 상세 이유)
                special_note=row["special_note"]     # 특이사항 (예: 감염병 의심, 면담 필요 등)
            )
            db.add(attendance)

    db.commit()
    db.close()
    print("✅ 출결 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_attendance()
