import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.students import Student as StudentModel  # ✅ 모델 import

CSV_PATH = "data/students.csv"  # ✅ 파일 경로

def migrate_students():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            student = StudentModel(
                id=int(row["id"]),                      # 고유 학생 ID
                student_name=row["student_name"],       # 학생 이름
                class_id=int(row["class_id"]),          # 소속 반 ID
                gender=row["gender"],                   # 성별 (예: 남, 여)
                phone=row["phone"],                     # 연락처
                address=row["address"]                  # 주소
            )
            db.add(student)

    db.commit()
    db.close()
    print("✅ 학생 정보 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_students()
