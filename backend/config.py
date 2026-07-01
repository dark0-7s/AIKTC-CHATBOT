# backend/config.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_cache_enabled: bool = True

    # Groq
    groq_api_key: str = ""

    # Database
    database_path: str = "data/aiktc.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    frontend_origin: str = "*"

    # KB
    kb_path: str = "data/kb"

    # Admin
    admin_user: str = "admin"
    admin_pass: str = "admin123"
    kb_reload_token: str = "secret-token"

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Demo mode (returns canned responses without Gemini)
    demo_mode: bool = False

    @property
    def resolved_kb_path(self) -> Path:
        return Path(self.kb_path)

    @property
    def resolved_database_path(self) -> Path:
        return Path(self.database_path)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()