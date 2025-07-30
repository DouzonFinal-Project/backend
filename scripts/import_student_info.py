import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.student_info import StudentInfo  # ✅ 새로운 모델 임포트

CSV_PATH = "data/student_info.csv"  # ✅ 파일 경로 확인

def migrate_student_info():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # CSV 필드와 모델 필드가 일치해야 함
            record = StudentInfo(
                student_id=int(row["student_id"]),
                student_name=row["student_name"],
                gender=row["gender"],
                phone=row["phone"],
                address=row["address"]
            )
            db.add(record)

    db.commit()
    db.close()
    print("✅ 학생 정보 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_student_info()
