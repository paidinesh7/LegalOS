"""Model mapping, API key handling, and pricing constants."""

from __future__ import annotations

import os
from dataclasses import dataclass


# ── Provider-aware model mapping ─────────────────────────────────

MODEL_MAP: dict[str, dict[str, str]] = {
    "anthropic": {
        "opus": "claude-opus-4-20250514",
        "sonnet": "claude-sonnet-4-20250514",
        "haiku": "claude-haiku-4-5-20251001",
    },
    "openai": {
        "o3": "o3",
        "4o": "gpt-4o",
        "4o-mini": "gpt-4o-mini",
    },
    "google": {
        "pro": "gemini-2.5-pro",
        "flash": "gemini-2.5-flash",
    },
}

DEFAULT_ALIAS: dict[str, str] = {
    "anthropic": "sonnet",
    "openai": "4o",
    "google": "flash",
}

# Environment variable name per provider
_API_KEY_ENV: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
}

# Pricing per million tokens (USD)
PRICING: dict[str, dict[str, float]] = {
    # Anthropic
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
    # OpenAI
    "o3": {
        "input": 10.0,
        "output": 40.0,
        "cache_write": 0.0,
        "cache_read": 0.0,
    },
    "gpt-4o": {
        "input": 2.50,
        "output": 10.0,
        "cache_write": 0.0,
        "cache_read": 0.0,
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
        "cache_write": 0.0,
        "cache_read": 0.0,
    },
    # Google
    "gemini-2.5-pro": {
        "input": 1.25,
        "output": 10.0,
        "cache_write": 0.0,
        "cache_read": 0.0,
    },
    "gemini-2.5-flash": {
        "input": 0.15,
        "output": 0.60,
        "cache_write": 0.0,
        "cache_read": 0.0,
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


def resolve_model(alias: str, provider: str = "anthropic") -> str:
    """Resolve a user-friendly alias to a full model ID.

    If *alias* is already a full model ID (not in MODEL_MAP), it is returned
    as-is so users can pass arbitrary model strings.
    """
    provider = provider.lower()
    if provider not in MODEL_MAP:
        raise ValueError(f"Unknown provider '{provider}'. Choose from: {', '.join(MODEL_MAP)}")
    provider_models = MODEL_MAP[provider]
    if alias in provider_models:
        return provider_models[alias]
    # Allow passing full model IDs directly (e.g. "gpt-4o-2024-08-06")
    return alias


def get_api_key(provider: str = "anthropic") -> str:
    """Get API key for the given provider from environment."""
    provider = provider.lower()
    env_var = _API_KEY_ENV.get(provider)
    if env_var is None:
        raise ValueError(f"Unknown provider '{provider}'. Choose from: {', '.join(_API_KEY_ENV)}")
    key = os.environ.get(env_var, "")
    if not key:
        raise EnvironmentError(
            f"{env_var} not set. Export it or add to .env file."
        )
    return key
