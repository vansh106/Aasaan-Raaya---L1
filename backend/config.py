from pydantic_settings import BaseSettings
from typing import Union, List, Optional
from pydantic import model_validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "ERP Agentic Chatbot API"
    app_version: str = "2.0.0"
    debug: bool = False

    # API Key Authentication
    api_key: str  # Required API key for authentication
    api_key_header_name: str = "X-API-Key"

    # LiteLLM Configuration - supports multiple providers
    # Examples: "gpt-4", "gpt-3.5-turbo", "gemini/gemini-2.0-flash", "claude-3-opus"
    llm_model: str = "gemini/gemini-2.0-flash"
    llm_api_key: str  # API key for the LLM provider (OpenAI, Gemini, Anthropic, etc.)
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    llm_timeout: int = 30

    # MongoDB Configuration
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "erp_chatbot"

    # ERP Configuration
    erp_base_url: str
    erp_api_timeout: int = 30

    # CORS - accepts comma-separated string from .env
    cors_origins: Union[str, List[str]] = "*"

    # Caching
    cache_ttl: int = 300  # Cache TTL in seconds (5 minutes)
    enable_cache: bool = True

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    @model_validator(mode="before")
    @classmethod
    def parse_cors(cls, values):
        """Parse CORS origins from comma-separated string"""
        if isinstance(values.get("cors_origins"), str):
            cors = values["cors_origins"]
            values["cors_origins"] = [origin.strip() for origin in cors.split(",")]
        return values

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
