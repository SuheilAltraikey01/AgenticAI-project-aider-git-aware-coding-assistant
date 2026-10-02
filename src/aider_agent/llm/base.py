from typing import Protocol


class LlmClient(Protocol):
    """Common interface for language model providers."""

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 800,
    ) -> str:
        """Generate a text response from the language model."""
        ...