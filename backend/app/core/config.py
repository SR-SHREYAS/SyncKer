"""Application configuration."""

import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "SyncSkill"
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/syncskill"
    )
    cors_allowed_origins: list[str] = Field(default_factory=list)
    jwt_secret_key: str = "change-me-please-use-a-long-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_allowed_origins(cls, value: object) -> list[str]:
        """Accept empty, comma-separated, or JSON-list CORS origin values."""
        if value is None:
            return []

        if isinstance(value, str):
            normalized_value = value.strip()
            if not normalized_value:
                return []
            if normalized_value.startswith(("[", "{")):
                try:
                    decoded_value = json.loads(normalized_value)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        "cors_allowed_origins must be a valid JSON array or comma-separated string"
                    ) from exc
                return cls._validate_cors_origins_list(decoded_value)
            return [
                origin.strip()
                for origin in normalized_value.split(",")
                if origin.strip()
            ]

        if isinstance(value, list):
            return cls._validate_cors_origins_list(value)

        raise ValueError(
            "cors_allowed_origins must be a list of strings, a JSON array, or a comma-separated string"
        )

    @classmethod
    def _validate_cors_origins_list(cls, value: object) -> list[str]:
        """Validate that decoded CORS origins are a list of strings."""
        if not isinstance(value, list):
            raise ValueError("cors_allowed_origins JSON value must decode to a list")
        if any(not isinstance(origin, str) for origin in value):
            raise ValueError("cors_allowed_origins list entries must all be strings")
        return [origin.strip() for origin in value if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
