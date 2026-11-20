"""
config.py
=========
LAYER: Configuration

Central settings — every env var lives here, read via pydantic-settings.
Override anything by setting the env var in .env or docker-compose.yml.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "Fraud Agentic AI"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # ── OpenAI ───────────────────────────────────────────────────────────────
    openai_api_key: str = Field(default="sk-mock-key", env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", env="OPENAI_MODEL")
    openai_temperature: float = 0.0
    openai_max_tokens: int = 2048

    # ── LangSmith ────────────────────────────────────────────────────────────
    langchain_tracing_v2: bool = Field(default=True, env="LANGCHAIN_TRACING_V2")
    langchain_api_key: str = Field(default="ls-mock-key", env="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="fraud-agentic-ai", env="LANGCHAIN_PROJECT")
    langchain_endpoint: str = Field(default="https://api.smith.langchain.com", env="LANGCHAIN_ENDPOINT")

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_ttl_seconds: int = Field(default=3600, env="REDIS_TTL_SECONDS")

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    chroma_host: str = Field(default="localhost", env="CHROMA_HOST")
    chroma_port: int = Field(default=8001, env="CHROMA_PORT")
    chroma_collection: str = Field(default="fraud_cases", env="CHROMA_COLLECTION")

    # ── MCP Servers ──────────────────────────────────────────────────────────
    banking_mcp_url: str = Field(default="http://localhost:8002", env="BANKING_MCP_URL")
    compliance_mcp_url: str = Field(default="http://localhost:8003", env="COMPLIANCE_MCP_URL")

    # ── Security ─────────────────────────────────────────────────────────────
    jwt_secret_key: str = Field(default="change-me-in-prod", env="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")

    # ── Observability ────────────────────────────────────────────────────────
    otel_endpoint: str = Field(default="http://localhost:4317", env="OTEL_ENDPOINT")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")

    # ── Evals ────────────────────────────────────────────────────────────────
    eval_dataset_path: str = Field(default="evals/eval_dataset.json", env="EVAL_DATASET_PATH")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
