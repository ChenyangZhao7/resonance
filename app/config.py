"""Application settings, read from environment variables.

Every value has a development-friendly default so the project still runs
out of the box, but secrets must be overridden in production.
"""

import os

try:  # optional: let a local .env file drive the settings
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - python-dotenv is optional
    pass

DEFAULT_SECRET_KEY = "dev-only-change-me-0123456789abcdef"


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class Settings:
    def __init__(self) -> None:
        # Auth
        self.secret_key: str = os.getenv("MRA_SECRET_KEY", DEFAULT_SECRET_KEY)
        self.algorithm: str = os.getenv("MRA_JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes: int = _env_int(
            "MRA_ACCESS_TOKEN_EXPIRE_MINUTES", 30
        )

        # Database
        self.database_url: str = os.getenv("MRA_DATABASE_URL", "sqlite:///./music.db")

        # Pagination / recommendation limits
        self.page_size_default: int = _env_int("MRA_PAGE_SIZE_DEFAULT", 20)
        self.page_size_max: int = _env_int("MRA_PAGE_SIZE_MAX", 100)
        self.recommend_limit_default: int = _env_int("MRA_RECOMMEND_LIMIT_DEFAULT", 10)
        self.recommend_limit_max: int = _env_int("MRA_RECOMMEND_LIMIT_MAX", 50)
        self.max_similar_candidates: int = _env_int("MRA_MAX_SIMILAR_CANDIDATES", 5000)

    @property
    def uses_default_secret(self) -> bool:
        return self.secret_key == DEFAULT_SECRET_KEY


settings = Settings()
