from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Resoft AI Delivery Studio API"
    debug: bool = False
    
    database_url: str = "postgresql+asyncpg://resoft:resoft_dev@localhost:5432/resoft_studio"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    access_token_expire_minutes: int = 60 * 24  # 1 day
    
    # ── OpenAI / AI Configuration ──
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_default_model: str = "gpt-4o"
    openai_default_temperature: float = 0.7
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
