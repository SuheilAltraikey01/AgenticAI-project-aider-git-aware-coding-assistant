class FakeLlmClient:
    """Offline LLM client used for deterministic tests."""

    def __init__(self, responses: list[str]):
        """
        Initialize the fake client with predefined responses.

        Args:
            responses:
                Responses that will be returned in order when
                generate() is called.
        """

        self._responses = list(responses)
        self.calls: list[dict] = []

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 800,
    ) -> str:
        """
        Return the next predefined response without calling a real API.

        Every call is recorded so tests can inspect what the agent
        sent to the language model.
        """

        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "max_tokens": max_tokens,
            }
        )

        if not self._responses:
            raise RuntimeError(
                "Fake LLM has no configured responses remaining."
            )

        return self._responses.pop(0)