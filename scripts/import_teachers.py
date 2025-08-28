import csv
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models import classes  # ✅ FK 대상 테이블 import
from models.teachers import Teacher as TeacherModel  # ✅ 모델 import

CSV_PATH = "data/teachers.csv"  # ✅ 파일 경로

def migrate_teachers():
    db: Session = SessionLocal()

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                teacher = TeacherModel(
                    id=int(row["id"]),                                # 교사 고유 ID
                    name=row["name"],                                 # 교사 이름
                    email=row["email"],                               # 이메일 주소
                    phone=row["phone"],                               # 연락처
                    subject=row["subject"],                           # 담당 과목 이름
                    role=row["role"],                                 # 교사 직책
                    is_homeroom=str(row["is_homeroom"]).strip().lower() in ("true", "1", "yes"),  # 담임 여부
                    homeroom_class=row["homeroom_class"] or None,     # 담임 학급명 (빈 문자열은 None)
                    class_id=int(float(row["class_id"])) if row["class_id"] else None  # 소수점 처리 포함
                )
                db.add(teacher)

            except Exception as e:
                print(f"⚠️ 오류 발생 (ID: {row.get('id')}): {e}")

    db.commit()
    db.close()
    print("✅ 교사 정보 CSV → DB 마이그레이션 완료")

if __name__ == "__main__":
    migrate_teachers()
