from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__", env_file=".env")

    chats_whitelist: list[int] = []
    gemini_key: str = ""
    tg_bot_key: str = ""
    summary_period: int = 24
    daily_hour: int = 22

    db_user: str = ""
    db_password: str = ""
    db_host: str = ""
    db_port: int = 0
    db_database: str = ""
    db_test: bool = False


settings = Settings()
