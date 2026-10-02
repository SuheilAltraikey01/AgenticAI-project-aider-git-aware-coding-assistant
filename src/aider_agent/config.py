import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Application configuration loaded from environment variables."""

    llm_provider: str
    llm_model: str
    deepseek_api_key: str | None

    def require_deepseek_api_key(self) -> str:
        """Return the DeepSeek API key or raise a clear configuration error."""

        api_key = self.deepseek_api_key

        if not api_key or api_key == "your_api_key_here":
            raise ValueError(
                "DEEPSEEK_API_KEY is missing. "
                "Add your real API key to the local .env file."
            )

        return api_key


def load_settings() -> Settings:
    """Load application settings from the local environment."""

    load_dotenv()

    return Settings(
        llm_provider=os.getenv(
            "LLM_PROVIDER",
            "deepseek",
        ).strip().lower(),
        llm_model=os.getenv(
            "LLM_MODEL",
            "deepseek-flash",
        ).strip(),
        deepseek_api_key=os.getenv(
            "DEEPSEEK_API_KEY"
        ),
    )