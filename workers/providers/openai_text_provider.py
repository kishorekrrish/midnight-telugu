"""OpenAI text provider — uses GPT models for script improvement."""

from __future__ import annotations

from workers.providers.base import BaseTextProvider


class OpenAITextProvider(BaseTextProvider):
    """Text provider backed by OpenAI's chat completion API."""

    def __init__(self) -> None:
        import os

        self._api_key = os.environ.get("OPENAI_API_KEY", "")
        self._model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

        if not self._api_key:
            raise ValueError("OPENAI_API_KEY not set")

    def generate_text(self, prompt: str) -> str:
        """Call OpenAI chat completion and return the response text."""
        # Import inside method so missing library doesn't break tests
        import openai  # type: ignore[import-untyped]  # noqa: PLC0415

        client = openai.OpenAI(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024,
        )
        text = response.choices[0].message.content or ""
        return text.strip()
