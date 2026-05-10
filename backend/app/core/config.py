from typing import Annotated, List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=True)

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str

    REDIS_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_TTL_MINUTES: int = 15
    REFRESH_TOKEN_TTL_DAYS: int = 7

    AWS_REGION: str
    AWS_ENDPOINT_URL: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    S3_BUCKET: str
    S3_TMP_PREFIX: str
    S3_SAMPLES_PREFIX: str
    S3_LANDING_PREFIX: str
    S3_RAW_PREFIX: str
    S3_CURATED_PREFIX: str
    S3_QUARANTINE_PREFIX: str
    S3_REPORTS_PREFIX: str
    S3_MAPPINGS_PREFIX: str

    DYNAMODB_TABLE: str
    GLUE_DATABASE: str
    SECRETS_PREFIX: str
    LAMBDA_TEST_CONNECTION_NAME: str

    AWS_REPORT_REGION: str
    AWS_REPORT_LAMBDA_NAME: str
    AWS_REPORT_S3_BUCKET: str
    AWS_REPORT_INVOKE_TIMEOUT_SECONDS: int = 120
    AWS_REPORT_PRESIGNED_URL_TTL_SECONDS: int = 600

    CORS_ORIGINS: Annotated[List[str], NoDecode] = ["http://localhost:5173"]
    VITE_API_BASE_URL: str = "http://localhost:8000/api/v1"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()  # pyright: ignore[reportCallIssue]  # values come from env at runtime
