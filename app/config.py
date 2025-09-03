from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "local"
    LOG_LEVEL: str = "INFO"

    API_MODE: str = "api-key"
    API_KEY: str = "change-me"
    CORS_ORIGINS: str = "http://localhost:3000"

    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_TIMEOUT_MS: int = 30000
    CONCURRENCY_MAX: int = 2
    PER_HOST_RPS: int = 4

    CONVERTER_DIR: str = "converter/images"
    RESULT_GIFS_DIR: str = "results/gifs"
    RESULT_VIDEOS_DIR: str = "results/videos"

    # Google Drive (optional)
    GOOGLE_DRIVE_ENABLED: bool = False
    GOOGLE_DRIVE_CREDENTIALS_JSON: str = "/app/creds/drive-creds.json"
    GOOGLE_DRIVE_DEFAULT_FOLDER_ID: str = ""
    GOOGLE_DRIVE_SHARE_ANYONE: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
