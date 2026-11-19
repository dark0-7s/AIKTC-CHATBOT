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
    admin_user: str = os.getenv("ADMIN_USER", "admin")
    admin_pass: str = os.getenv("ADMIN_PASS", "admin123")
    kb_reload_token: str = os.getenv("KB_RELOAD_TOKEN", "my-secret-token")

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Demo mode (returns canned responses without Gemini)
    demo_mode: bool = False

    @property
    def resolved_kb_path(self) -> Path:
        p = Path(self.kb_path)
        if not p.is_absolute():
            base = Path(__file__).resolve().parent
            if (base / p).exists():
                return base / p
        return p

    @property
    def resolved_database_path(self) -> Path:
        p = Path(self.database_path)
        if not p.is_absolute():
            base = Path(__file__).resolve().parent
            return base / p
        return p

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()