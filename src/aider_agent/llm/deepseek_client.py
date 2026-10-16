from time import perf_counter

from openai import OpenAI, OpenAIError


class DeepSeekClient:
    """DeepSeek API client with usage and latency tracking."""

    BASE_URL = "https://api.deepseek.com"

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-flash",
    ):
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

        # Successful API calls.
        self.usage_records: list[dict] = []

        # Failed API requests.
        self.failed_request_records: list[dict] = []

    def _usage_value(
        self,
        usage,
        name: str,
    ) -> int:
        """Safely read an integer usage field."""

        if usage is None:
            return 0

        value = getattr(
            usage,
            name,
            0,
        )

        return int(
            value or 0
        )

    def _record_usage(
        self,
        response,
        latency_seconds: float,
    ) -> None:
        """Record token usage and latency for one API call."""

        usage = getattr(
            response,
            "usage",
            None,
        )

        prompt_tokens = self._usage_value(
            usage,
            "prompt_tokens",
        )

        completion_tokens = self._usage_value(
            usage,
            "completion_tokens",
        )

        total_tokens = self._usage_value(
            usage,
            "total_tokens",
        )

        cache_hit_tokens = self._usage_value(
            usage,
            "prompt_cache_hit_tokens",
        )

        cache_miss_tokens = self._usage_value(
            usage,
            "prompt_cache_miss_tokens",
        )

        # Compatibility fallback.
        if (
            prompt_tokens > 0
            and cache_hit_tokens == 0
            and cache_miss_tokens == 0
        ):
            prompt_details = getattr(
                usage,
                "prompt_tokens_details",
                None,
            )

            cached_tokens = getattr(
                prompt_details,
                "cached_tokens",
                0,
            )

            cache_hit_tokens = int(
                cached_tokens or 0
            )

            cache_miss_tokens = max(
                prompt_tokens
                - cache_hit_tokens,
                0,
            )

        completion_details = getattr(
            usage,
            "completion_tokens_details",
            None,
        )

        reasoning_tokens = int(
            getattr(
                completion_details,
                "reasoning_tokens",
                0,
            )
            or 0
        )

        self.usage_records.append(
            {
                "model": getattr(
                    response,
                    "model",
                    self.model,
                ),
                "latency_seconds":
                    latency_seconds,
                "prompt_tokens":
                    prompt_tokens,
                "prompt_cache_hit_tokens":
                    cache_hit_tokens,
                "prompt_cache_miss_tokens":
                    cache_miss_tokens,
                "completion_tokens":
                    completion_tokens,
                "reasoning_tokens":
                    reasoning_tokens,
                "total_tokens":
                    total_tokens,
            }
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 800,
    ) -> str:
        """Generate one DeepSeek response."""

        started_at = perf_counter()

        try:
            response = (
                self._client
                .chat
                .completions
                .create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content":
                                system_prompt,
                        },
                        {
                            "role": "user",
                            "content":
                                user_prompt,
                        },
                    ],
                    max_tokens=max_tokens,
                    extra_body={
                        "thinking": {
                            "type": "disabled"
                        }
                    },
                )
            )

        except OpenAIError as exc:
            latency_seconds = (
                perf_counter()
                - started_at
            )

            self.failed_request_records.append(
                {
                    "model":
                        self.model,
                    "latency_seconds":
                        latency_seconds,
                    "error_type":
                        type(exc).__name__,
                }
            )

            raise RuntimeError(
                "DeepSeek API request failed."
            ) from exc

        latency_seconds = (
            perf_counter()
            - started_at
        )

        self._record_usage(
            response=response,
            latency_seconds=latency_seconds,
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if not content:
            finish_reason = (
                response
                .choices[0]
                .finish_reason
            )

            raise RuntimeError(
                "DeepSeek API returned an empty response. "
                f"Finish reason: {finish_reason}"
            )

        return content.strip()