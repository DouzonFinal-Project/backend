# .env 파일에 정의된 환경변수를 읽어와 사용하기 위한 설정 파일입니다.

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_USER: str         # MySQL 사용자 이름
    DB_PASSWORD: str     # MySQL 비밀번호
    DB_HOST: str         # 데이터베이스 호스트
    DB_PORT: str         # 포트 번호
    DB_NAME: str         # 데이터베이스 이름

    # ✅ 전체 접속 URL을 동적으로 생성
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"  # ✅ 환경변수를 불러올 .env 파일 지정

# ✅ settings 객체를 통해 어디서든 접근 가능
settings = Settings()
