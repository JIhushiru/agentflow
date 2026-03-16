from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "AGENTFLOW_", "env_file": ".env"}

    # LLM provider: "ollama" (free, local), "anthropic" (Claude API), or "groq" (Groq API)
    llm_provider: Literal["ollama", "anthropic", "groq"] = "ollama"

    # Ollama (default — free)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Anthropic (optional)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Groq (optional)
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"

    @property
    def default_model(self) -> str:
        if self.llm_provider == "anthropic":
            return self.anthropic_model
        if self.llm_provider == "groq":
            return self.groq_model
        return self.ollama_model

    @property
    def planner_model(self) -> str:
        return self.default_model

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentflow"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]

    # Agent execution
    agent_timeout_seconds: int = 120
    max_retries: int = 2


settings = Settings()
