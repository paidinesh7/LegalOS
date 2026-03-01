"""Anthropic SDK wrapper with prompt caching, retries, and structured output."""

from __future__ import annotations

import json
import time
from typing import TypeVar, Type

import anthropic
from pydantic import BaseModel

from legalos.config import TokenUsage, get_api_key
from legalos.utils.errors import APIError

T = TypeVar("T", bound=BaseModel)

# Retry config
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


class AnalysisClient:
    """Wraps the Anthropic SDK with prompt caching and structured output."""

    def __init__(self, model_id: str, verbose: bool = False) -> None:
        self.model_id = model_id
        self.verbose = verbose
        self.usage = TokenUsage()
        self._client = anthropic.Anthropic(
            api_key=get_api_key(),
            max_retries=0,  # We handle retries ourselves
        )

    def analyze(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        document_text: str | None = None,
    ) -> T:
        """Run an analysis call with prompt caching and structured output.

        The system_prompt + document_text are cached across calls.
        Returns a parsed Pydantic model.
        """
        # Build system messages with cache control
        system_parts: list[dict] = []
        system_parts.append({
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        })
        if document_text:
            system_parts.append({
                "type": "text",
                "text": f"<document>\n{document_text}\n</document>",
                "cache_control": {"type": "ephemeral"},
            })

        # User message with JSON schema instruction
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        user_content = (
            f"{user_prompt}\n\n"
            f"Respond with valid JSON matching this schema:\n"
            f"```json\n{schema_json}\n```\n\n"
            f"Output ONLY the JSON object, no other text."
        )

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.messages.create(
                    model=self.model_id,
                    max_tokens=8192,
                    system=system_parts,
                    messages=[{"role": "user", "content": user_content}],
                )
                break
            except anthropic.RateLimitError as e:
                last_error = e
                wait = RETRY_BACKOFF * (attempt + 1)
                if self.verbose:
                    print(f"  Rate limited, retrying in {wait}s…")
                time.sleep(wait)
            except anthropic.APIError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF)
                continue
        else:
            raise APIError(f"API call failed after {MAX_RETRIES} retries: {last_error}")

        # Track token usage
        usage = response.usage
        self.usage.add(
            input_t=usage.input_tokens,
            output_t=usage.output_tokens,
            cache_write=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            cache_read=getattr(usage, "cache_read_input_tokens", 0) or 0,
        )

        # Parse response
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()

        try:
            return response_model.model_validate_json(text)
        except Exception as e:
            raise APIError(f"Failed to parse response as {response_model.__name__}: {e}\nRaw: {text[:500]}")

    def chat(
        self,
        system_prompt: str,
        messages: list[dict],
        document_text: str | None = None,
    ) -> str:
        """Simple chat call for Q&A (no structured output)."""
        system_parts: list[dict] = []
        system_parts.append({
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        })
        if document_text:
            system_parts.append({
                "type": "text",
                "text": f"<document>\n{document_text}\n</document>",
                "cache_control": {"type": "ephemeral"},
            })

        response = self._client.messages.create(
            model=self.model_id,
            max_tokens=4096,
            system=system_parts,
            messages=messages,
        )

        usage = response.usage
        self.usage.add(
            input_t=usage.input_tokens,
            output_t=usage.output_tokens,
            cache_write=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            cache_read=getattr(usage, "cache_read_input_tokens", 0) or 0,
        )

        return response.content[0].text
