from sqlalchemy import create_engine               # SQLAlchemy 엔진 생성 도구
from sqlalchemy.ext.declarative import declarative_base  # 모델의 Base 클래스
from sqlalchemy.orm import sessionmaker            # 세션 팩토리 함수

from config.settings import settings               # ✅ 환경변수 설정 파일 불러오기

# ✅ 환경변수에서 DB 연결 URL을 불러와 엔진 생성
engine = create_engine(settings.DATABASE_URL)

# ✅ 세션 팩토리: DB 연결에 사용할 세션 생성기 정의
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ 모델 정의 시 상속할 Base 클래스 (Declarative 방식 사용)
Base = declarative_base()
