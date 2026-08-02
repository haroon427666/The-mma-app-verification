"""Application settings from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Application
    app_name: str = "MMA Backend"
    environment: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://mma:mma@localhost:5432/mma"

    # Auth
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    sliding_refresh_window_minutes: int = 2

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # ESPN
    espn_base_url: str = "https://sports.core.api.espn.com/v2/sports/mma"
    espn_rate_limit: float = 10.0
    espn_page_limit: int = 100

    # TheSportsDB
    tsdb_base_url: str = "https://www.thesportsdb.com/api/v1/json"
    tsdb_api_key: str = "3"
    tsdb_rate_limit_per_minute: int = 25

    # Octagon API
    octagon_base_url: str = "https://api.octagon-api.com"

    # Sync
    sync_default_provider: str = "espn"
    sync_batch_size: int = 500

    # Cron
    cron_full_sync: str = "0 2 * * *"       # Daily 2 AM
    cron_rankings_sync: str = "0 */6 * * *"  # Every 6 hours
    cron_events_sync: str = "*/30 * * * *"   # Every 30 minutes (fight nights)
    cron_enrichment_sync: str = "0 5 * * 0" # Weekly Sunday 5 AM


settings = Settings()
