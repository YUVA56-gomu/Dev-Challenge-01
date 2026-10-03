from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Sathi AI CA Companion"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma2:2b"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

settings = Settings()
