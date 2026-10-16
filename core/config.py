"""core/config.py - Centralized Pydantic Settings for Aegis."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # Daytona
    DAYTONA_API_KEY: str = Field(default="mock_daytona_key")
    DAYTONA_SERVER_URL: str = Field(default="https://app.daytona.io/api")
    DAYTONA_TARGET: str = Field(default="us")

    # ElevenLabs
    ELEVENLABS_API_KEY: str = Field(default="mock_elevenlabs_key")
    ELEVENLABS_VOICE_ID: str = Field(default="21m00Tcm4TlvDq8ikWAM")
    ELEVENLABS_MODEL_ID: str = Field(default="eleven_turbo_v2_5")

    # Arize AI Phoenix
    PHOENIX_COLLECTOR_ENDPOINT: str = Field(default="http://localhost:6006")
    PHOENIX_PROJECT_NAME: str = Field(default="aegis-voice-sre")

    # Anchor Browser
    ANCHOR_API_KEY: str = Field(default="mock_anchor_key")
    ANCHOR_CDP_URL: str = Field(default="wss://connect.anchorbrowser.io")

    # SurrealDB
    SURREALDB_URL: str = Field(default="ws://localhost:8000/rpc")
    SURREALDB_USER: str = Field(default="root")
    SURREALDB_PASS: str = Field(default="root")
    SURREALDB_NS: str = Field(default="aegis")
    SURREALDB_DB: str = Field(default="incidents")

    # AWS Bedrock
    AWS_DEFAULT_REGION: str = Field(default="us-west-2")
    AWS_REGION: str = Field(default="us-west-2")
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
    AWS_SESSION_TOKEN: str = Field(default="")
    AWS_BEARER_TOKEN_BEDROCK: str = Field(default="")
    BEDROCK_MODEL_ID: str = Field(default="anthropic.claude-3-5-sonnet-20240620-v1:0")

    # Fallback / Mock Mode for Stage Demo. True skips live Phoenix export.
    IS_MOCK_MODE: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
