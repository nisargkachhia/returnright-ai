"""Typed environment-based settings."""

from datetime import datetime
from enum import Enum
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.domain.clock import DEMO_AS_OF


class AppEnv(str, Enum):
    development = "development"
    production = "production"
    test = "test"


class Settings(BaseSettings):
    """Runtime settings loaded from the environment or a .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ReturnRight AI"
    app_env: AppEnv = AppEnv.development
    log_level: str = "INFO"
    demo_mode: bool = True
    demo_user_id: str = "demo-user-1"
    demo_user_display_name: str = "Alex Demo"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    database_url: str = "sqlite:///./data/returnright.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    mcp_stateless_http: bool = True
    mcp_json_response: bool = True
    confirmation_token_ttl_seconds: int = 900
    policy_as_of: datetime = Field(default_factory=lambda: DEMO_AS_OF)

    @field_validator("database_url")
    @classmethod
    def database_url_required(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("DATABASE_URL is required")
        return value.strip()

    @field_validator("demo_user_id")
    @classmethod
    def demo_user_required(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("DEMO_USER_ID is required")
        return value.strip()

    @field_validator("backend_port")
    @classmethod
    def port_range(cls, value: int) -> int:
        if value < 1 or value > 65535:
            raise ValueError("BACKEND_PORT must be between 1 and 65535")
        return value

    @field_validator("confirmation_token_ttl_seconds")
    @classmethod
    def ttl_positive(cls, value: int) -> int:
        if value < 60:
            raise ValueError("CONFIRMATION_TOKEN_TTL_SECONDS must be at least 60")
        return value

    @field_validator("policy_as_of")
    @classmethod
    def policy_as_of_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            from datetime import timezone

            return value.replace(tzinfo=timezone.utc)
        return value

    @model_validator(mode="after")
    def production_guardrails(self) -> "Settings":
        if self.app_env == AppEnv.production:
            if "*" in self.cors_origins:
                raise ValueError("production CORS_ORIGINS cannot contain '*'")
            if not self.database_url.startswith(("sqlite:///", "postgresql")):
                raise ValueError("production DATABASE_URL must be sqlite or postgresql")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnv.production


@lru_cache
def get_settings() -> Settings:
    return Settings()
