from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SAIMOO_ENV: str = "development"
    DB_URL: str = "sqlite:///./saimoo.db"
    TUSHARE_TOKEN: str = ""
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
