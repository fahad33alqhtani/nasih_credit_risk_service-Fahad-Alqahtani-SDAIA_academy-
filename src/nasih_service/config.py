"""Typed settings, read once from the environment with the NASIH_ prefix."""
from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NASIH_")

    model_path: str = "models/credit_model.json"
    reject_threshold: float = Field(default=0.70, ge=0.0, le=1.0)
    redis_url: str = "redis://localhost:6379/0"
    audit_ttl_seconds: int = Field(default=60 * 60 * 24, gt=0)
    log_level: str = "INFO"

    @field_validator("redis_url")
    @classmethod
    def _validate_redis_url(cls, v: str) -> str:
        # A typo'd URL should stop the process at boot rather than
        # surface as a connection error on the first request.
        AnyUrl(v)
        if not v.startswith("redis://") and not v.startswith("rediss://"):
            raise ValueError("redis_url must start with redis:// or rediss://")
        return v


settings = Settings()
