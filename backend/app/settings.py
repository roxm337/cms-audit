from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Project configuration loaded from environment variables or `.env`."""

    # Database
    database_url: str = Field(
        "mysql+pymysql://user:password@localhost/vulntracker",
        env="DATABASE_URL",
    )

    # Celery / Redis
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    # Auth (for future JWT implementation)
    secret_key: str = Field("change-me", env="SECRET_KEY")

    # External APIs
    wpscan_token: str = Field(..., env="WPSCAN_TOKEN")  # free token OK

    class Config:
        env_file = ".env"

settings = Settings()
