"""Configuracion de runtime cargada desde entorno y archivo .env local."""

from typing import ClassVar, Literal

from dotenv import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_ = load_dotenv()


class Settings(BaseSettings):
    """Variables de entorno necesarias para API, CORS y proveedor LLM."""

    API_KEY: SecretStr | None = None
    NOVITA_API_KEY: SecretStr
    NOVITA_BASE_URL: str = "https://api.novita.ai/openai/v1"
    ENV: Literal["development", "production"] = "production"

    CORS_ALLOW_ORIGINS: list[str] = [
        "http://localhost:4321",
        "https://patagonia.luka.software",
    ]

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", extra="ignore"
    )


settings = Settings()  # pyright: ignore[reportCallIssue]
