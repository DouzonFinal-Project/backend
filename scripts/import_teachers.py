import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.teachers import Teacher as TeacherModel  # ✅ 모델 import

CSV_PATH = "data/teachers.csv"  # ✅ 파일 경로

def migrate_teachers():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            teacher = TeacherModel(
                id=int(row["id"]),              # 교사 고유 ID
                name=row["name"],               # 교사 이름
                email=row["email"],             # 이메일 주소
                phone=row["phone"],             # 연락처
                subject=row["subject"]          # 담당 과목 이름
            )
            db.add(teacher)

    db.commit()
    db.close()
    print("✅ 교사 정보 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_teachers()
