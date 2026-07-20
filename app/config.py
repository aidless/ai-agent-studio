"""AI Agent Studio - 全局配置"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    app_name: str = "AI Agent Studio"
    app_version: str = "3.0.0"

    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")  # SECURITY: never hardcode API keys; set DEEPSEEK_API_KEY env var
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    chroma_persist_dir: str = os.getenv("CHROMA_DIR", str(BASE_DIR / "data" / "chroma"))
    knowledge_dir: str = os.getenv("KNOWLEDGE_DIR", str(BASE_DIR / "data" / "knowledge"))

    port: int = int(os.getenv("PORT", "8000"))
    host: str = os.getenv("HOST", "0.0.0.0")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    max_tokens: int = 2048
    temperature: float = 0.7
    request_timeout: int = 120

    class Config:
        env_file = ".env"

settings = Settings()
