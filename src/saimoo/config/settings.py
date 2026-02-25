from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    # Database
    DB_PATH: str = "saimoo.db"

    @property
    def DB_URL(self) -> str:
        """Construct database URL from path"""
        return f"sqlite:///{self.DB_PATH}"

    # Data Sources
    TUSHARE_TOKEN: str = ""
    RQDATA_USER: str = ""
    RQDATA_PASSWORD: str = ""

    # Backtest
    DEFAULT_CAPITAL: float = 100000.0
    DEFAULT_COMMISSION: float = 0.0003

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
