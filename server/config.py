from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_prefix: str = "/api/1.0"
    jwt_secret: str = "76fc1e12fb51885f0bc8c570421436fab44673e9b91eca7b11212a90a22e1fb9"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_s: int = 15 * 60
    jwt_refresh_ttl_s: int = 30 * 24 * 60 * 60


settings = Settings()
