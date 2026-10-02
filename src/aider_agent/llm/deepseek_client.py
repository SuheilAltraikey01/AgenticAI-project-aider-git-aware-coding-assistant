from openai import OpenAI, OpenAIError


class DeepSeekClient:
    """Client for communicating with the DeepSeek API."""

    BASE_URL = "https://api.deepseek.com"

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-flash",
    ):
        """
        Initialize the DeepSeek client.

        Args:
            api_key:
                DeepSeek API key loaded from the environment.

            model:
                DeepSeek model name used for requests.
        """

        if not api_key.strip():
            raise ValueError(
                "DeepSeek API key cannot be empty."
            )

        self.model = model

        self._client = OpenAI(
            api_key=api_key,
            base_url=self.BASE_URL,
            timeout=30.0,
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 800,
    ) -> str:
        """
        Send a request to DeepSeek and return the generated text.

        Thinking mode is disabled for this basic provider integration.
        The model only returns text and cannot directly modify files.
        """

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                max_tokens=max_tokens,
                extra_body={
                    "thinking": {
                        "type": "disabled"
                    }
                },
            )

        except OpenAIError as exc:
            raise RuntimeError(
                "DeepSeek API request failed."
            ) from exc

        content = response.choices[0].message.content

        if not content:
            finish_reason = response.choices[0].finish_reason

            raise RuntimeError(
                "DeepSeek API returned an empty response. "
                f"Finish reason: {finish_reason}"
            )

        return content.strip()