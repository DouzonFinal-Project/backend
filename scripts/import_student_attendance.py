import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.student_attendance import StudentAttendance  # ✅ 모델 임포트

CSV_PATH = "data/student_attendance.csv"  # ✅ 파일 경로 확인

def migrate_student_attendance():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            record = StudentAttendance(
                student_id=int(row["student_id"]),        # 학생 고유 ID
                student_name=row["student_name"],          # 학생 이름
                date=row["date"],                          # 출결 일자
                status=row["status"],                      # 출결 상태
                reason=row["reason"]                       # 출결 사유
            )
            db.add(record)

    db.commit()
    db.close()
    print("✅ 출결 정보 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_student_attendance()
