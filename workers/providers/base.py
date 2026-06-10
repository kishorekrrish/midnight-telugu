"""Abstract base class for text generation providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseTextProvider(ABC):
    """Abstract text generation provider."""

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """Generate text from a prompt. Returns non-empty string."""
        ...
