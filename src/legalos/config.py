"""Model mapping, API key handling, and pricing constants."""

from __future__ import annotations

import os
from dataclasses import dataclass


MODEL_MAP: dict[str, str] = {
    "opus": "claude-opus-4-20250514",
    "sonnet": "claude-sonnet-4-20250514",
    "haiku": "claude-haiku-4-5-20251001",
}

# Pricing per million tokens (USD)
PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-20250514": {
        "input": 15.0,
        "output": 75.0,
        "cache_write": 18.75,
        "cache_read": 1.50,
    },
    "claude-sonnet-4-20250514": {
        "input": 3.0,
        "output": 15.0,
        "cache_write": 3.75,
        "cache_read": 0.30,
    },
    "claude-haiku-4-5-20251001": {
        "input": 0.80,
        "output": 4.0,
        "cache_write": 1.0,
        "cache_read": 0.08,
    },
}

# Token thresholds for chunking
SINGLE_PASS_LIMIT = 150_000
MAX_DOCUMENT_TOKENS = 500_000
CHUNK_OVERLAP = 2_000


@dataclass
class TokenUsage:
    """Tracks cumulative token usage across API calls."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0

    def add(self, input_t: int, output_t: int, cache_write: int = 0, cache_read: int = 0) -> None:
        self.input_tokens += input_t
        self.output_tokens += output_t
        self.cache_write_tokens += cache_write
        self.cache_read_tokens += cache_read

    def cost(self, model_id: str) -> float:
        p = PRICING.get(model_id, PRICING["claude-sonnet-4-20250514"])
        return (
            self.input_tokens * p["input"] / 1_000_000
            + self.output_tokens * p["output"] / 1_000_000
            + self.cache_write_tokens * p["cache_write"] / 1_000_000
            + self.cache_read_tokens * p["cache_read"] / 1_000_000
        )

    def summary(self, model_id: str) -> str:
        return (
            f"Tokens — in: {self.input_tokens:,}  out: {self.output_tokens:,}  "
            f"cache_write: {self.cache_write_tokens:,}  cache_read: {self.cache_read_tokens:,}  "
            f"cost: ${self.cost(model_id):.4f}"
        )


def resolve_model(alias: str) -> str:
    """Resolve a user-friendly alias to a full model ID."""
    if alias in MODEL_MAP:
        return MODEL_MAP[alias]
    raise ValueError(f"Unknown model alias '{alias}'. Choose from: {', '.join(MODEL_MAP)}")


def get_api_key() -> str:
    """Get Anthropic API key from environment."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. Export it or add to .env file."
        )
    return key
