"""Configuration settings for the synthetic target application.

All settings are explicitly scoped to local testing and research evaluation.
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or defaults."""

    app_env: str = Field(default="development", description="Application environment")
    app_host: str = Field(default="127.0.0.1", description="Host to bind server")
    app_port: int = Field(default=8000, description="Port to bind server")
    db_path: str = Field(default="./synthetic_data.db", description="Path to SQLite database file")

    # Local research test tokens mapping token string -> principal_id
    # Scoped strictly to deterministic offline evaluation harness; NOT for production use.
    test_token_user_a: str = "test-token-user-a"
    test_token_user_b: str = "test-token-user-b"
    test_token_user_c: str = "test-token-user-c"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def token_principal_map(self) -> dict[str, str]:
        """Deterministic mapping of local test bearer tokens to synthetic user principals."""
        return {
            self.test_token_user_a: "user_a",
            self.test_token_user_b: "user_b",
            self.test_token_user_c: "user_c",
        }

    @property
    def resolved_db_path(self) -> Path:
        """Resolve database path relative to project root or absolute."""
        p = Path(self.db_path)
        if not p.is_absolute():
            return p.resolve()
        return p


settings = Settings()

