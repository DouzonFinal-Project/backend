"""
config/settings.py

- .env에 정의한 환경변수를 읽어 애플리케이션 전역 설정으로 제공합니다.
- pydantic v2 / pydantic-settings v2 사용.
- DB URL은 부분 값(DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME)로부터 동적으로 구성하며,
  레거시 호환을 위해 DATABASE_URL, DB_URL 두 이름 모두 제공(@computed_field).
"""

from typing import List, Optional, Literal
from pydantic import field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================
    # 앱/런타임
    # =========================
    ENV: Literal["dev", "stage", "prod"] = "dev"
    APP_TITLE: str = "Teacher Assistant API"
    APP_DESCRIPTION: str = "초등학교 교사 행정지원 AI 챗봇 백엔드 API"
    APP_VERSION: str = "1.0.0"

    # =========================
    # CORS
    # =========================
    # 콤마(,)로 구분된 문자열 → List[str] 로 파싱
    CORS_ORIGINS: List[str] = ["http://3.34.241.88:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            # "a,b , c" → ["a","b","c"]
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    # =========================
    # Database (MySQL)
    # =========================
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int = 3307
    DB_NAME: str

    # 레거시 호환 & 명확한 명칭 둘 다 제공
    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URL(self) -> str:
        """
        레거시 호환용 속성명. 내부적으로 DB_URL과 동일한 값을 반환.
        비밀번호에 URL 인코딩 문자가 포함되어 있어도 그대로 사용(이미 인코딩했다면 중복 인코딩 방지).
        예: mysql+pymysql://user:P%40ssw0rd@host:3306/db
        """
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field  # type: ignore[misc]
    @property
    def DB_URL(self) -> str:
        """
        권장 속성명. DATABASE_URL과 동일값. 코드에서 self.DB_URL로 사용 가능.
        """
        return self.DATABASE_URL

    # =========================
    # Front API
    # =========================
    FRONT_API_BASE_URL: str
    FRONT_INTERNAL_TOKEN: str


    # =========================
    # LLM (Gemini only)
    # =========================
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_API_KEY: str  # 필수
    LLM_TIMEOUT: int = 25
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 1024
    LLM_API_BASE_URL: str  
    LLM_INTERNAL_TOKEN: str 

    # =========================
    # Vector DB (Milvus)
    # =========================
    MILVUS_HOST: str = "10.0.141.42"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "docs_v1"
    MILVUS_DIM: int = 768
    MILVUS_INDEX: Literal["HNSW", "IVF_FLAT", "IVF_SQ8", "DISKANN", "FLAT"] = "HNSW"
    MILVUS_METRIC: Literal["IP", "COSINE", "L2"] = "IP"

    # =========================
    # Object Storage (MinIO / S3 호환)
    # =========================
    MINIO_ENDPOINT: str = "10.0.141.42:9000"  # 예: "minio:9000" 또는 "play.min.io:9000"
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: str = "admin1234"
    MINIO_BUCKET: str = "teacher-docs"
    MINIO_SECURE: bool = False  # http=False, https=True

    # =========================
    # PDF / WeasyPrint (선택)
    # =========================
    WEASYPRINT_FONT_DIR: Optional[str] = None

    # =========================
    # Logging / Misc
    # =========================
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    REQUEST_LOG_JSON: bool = True
    MAX_UPLOAD_MB: int = 20

    # =========================
    # BaseSettings Config
    # =========================
    model_config = SettingsConfigDict(
        env_file=".env",               # .env에서 값 로드
        env_file_encoding="utf-8",
        case_sensitive=False,          # 환경변수 대소문자 비구분 (원하면 True로)
        extra="ignore",                # 정의되지 않은 키는 무시
    )


# ✅ settings 객체를 통해 어디서든 접근 가능
settings = Settings()
