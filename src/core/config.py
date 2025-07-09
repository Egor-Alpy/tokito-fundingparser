from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "TokitoFundParser"
    API_ID: int = 12345678  # API ID  my.telegram.org
    API_HASH: str = "hash_from_my.telegram.org" # API HASH my.telegram.org
    SESSION_NAME: str = "tg_session"  # Имя для файла сессии телеграмма
    CHAT_ID: str = "@fundparser"  # Чат, куда будут отправляться сообщения (username with @ or numeric ID)
    CHECK_DELAY: int = 15  # Задержка в СЕКУНДАХ между запросами на получение последних фандингов11
    SIZE_OF_TEMPORAL_FUNDS_STORAGE: int = 100  # Количество key + stage последних фандингов, которые мы запоминаем

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
