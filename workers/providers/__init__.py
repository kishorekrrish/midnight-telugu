"""Provider factory for text generation backends."""

from __future__ import annotations

from workers.providers.base import BaseTextProvider
from workers.providers.mock_text_provider import MockTextProvider


def get_text_provider(provider_name: str) -> BaseTextProvider:
    """Return the appropriate text provider instance."""
    if provider_name == "openai":
        from workers.providers.openai_text_provider import OpenAITextProvider

        return OpenAITextProvider()
    if provider_name == "mock":
        return MockTextProvider()
    raise ValueError(f"Text provider '{provider_name}' is not implemented.")


__all__ = ["BaseTextProvider", "MockTextProvider", "get_text_provider"]
