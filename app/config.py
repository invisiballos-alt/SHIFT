from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/booking_db"

    class Config:
        env_file = ".env"

settings = Settings()
