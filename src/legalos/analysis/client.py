"""Anthropic SDK wrapper with prompt caching, retries, and structured output."""

from __future__ import annotations

import json
import re
import time
from typing import TypeVar, Type

import anthropic
from pydantic import BaseModel

from legalos.config import TokenUsage, get_api_key
from legalos.utils.errors import APIError

T = TypeVar("T", bound=BaseModel)

# Retry config
MAX_RETRIES = 8
RETRY_BACKOFF = 2.0
MAX_BACKOFF = 90.0

# Rate-limit pacing: minimum seconds between API calls.
# Set >0 for low-tier accounts (e.g. 20 for 4K output tokens/min limit).
_MIN_CALL_INTERVAL = 20.0


def _repair_truncated_json(text: str) -> str:
    """Best-effort repair of JSON truncated mid-stream.

    Counts open braces/brackets and appends closing tokens to make it
    valid.  Truncated strings are closed with a quote first.
    """
    # Strip trailing incomplete escape sequences
    text = re.sub(r'\\$', '', text)

    # If we're inside an unclosed string, close it
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
    if in_string:
        text += '"'

    # Count unmatched openers
    stack: list[str] = []
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in ('{', '['):
            stack.append(ch)
        elif ch == '}' and stack and stack[-1] == '{':
            stack.pop()
        elif ch == ']' and stack and stack[-1] == '[':
            stack.pop()

    # Close in reverse order
    for opener in reversed(stack):
        text += ']' if opener == '[' else '}'

    return text


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
        self._last_call_time: float = 0.0
        self._call_interval: float = _MIN_CALL_INTERVAL

    def _pace(self) -> None:
        """Wait if needed to respect rate limits between calls."""
        if self._call_interval > 0 and self._last_call_time > 0:
            elapsed = time.time() - self._last_call_time
            if elapsed < self._call_interval:
                wait = self._call_interval - elapsed
                if self.verbose:
                    print(f"  Pacing: waiting {wait:.1f}s between calls…")
                time.sleep(wait)

    def analyze(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        document_text: str | None = None,
        max_tokens: int = 1024,
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

        # User message with JSON schema instruction — keep output tiny
        schema_json = json.dumps(response_model.model_json_schema())

        # Only apply finding-specific limits when response model has findings
        finding_rules = ""
        if hasattr(response_model, "model_fields") and "findings" in response_model.model_fields:
            finding_rules = (
                "- Max 2 findings. Only the 2 most critical issues.\n"
                "- quoted_text: max 50 chars, just enough to identify the clause.\n"
                "- why_it_matters: max 25 words combining what it means and founder impact.\n"
                "- action: max 15 words, imperative (what to negotiate/do).\n"
            )

        user_content = (
            f"{user_prompt}\n\n"
            f"Respond with ONLY a JSON object matching this schema:\n"
            f"{schema_json}\n\n"
            f"CRITICAL OUTPUT RULES — you MUST follow these to avoid truncation:\n"
            f"{finding_rules}"
            f"- summary: max 1 sentence, under 20 words.\n"
            f"- If this is an explainer: max 5 terms, each definition under 20 words.\n"
            f"- If this is impact assessment: max 3 negotiation items, "
            f"each field under 15 words. Max 3 waterfall rows.\n"
            f"- No markdown, no extra text, ONLY the JSON."
        )

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            self._pace()
            try:
                response = self._client.messages.create(
                    model=self.model_id,
                    max_tokens=max_tokens,
                    system=system_parts,
                    messages=[{"role": "user", "content": user_content}],
                )
                self._last_call_time = time.time()

                # Track token usage
                u = response.usage
                self.usage.add(
                    input_t=u.input_tokens, output_t=u.output_tokens,
                    cache_write=getattr(u, "cache_creation_input_tokens", 0) or 0,
                    cache_read=getattr(u, "cache_read_input_tokens", 0) or 0,
                )

                # If output was truncated, try to salvage the partial JSON
                truncated = response.stop_reason == "max_tokens"
                if truncated and self.verbose:
                    print("  Output truncated — attempting to repair partial JSON…")

                break  # Got a response (truncated or not), try to parse it

            except anthropic.RateLimitError as e:
                last_error = e
                wait = min(RETRY_BACKOFF * (2 ** attempt), MAX_BACKOFF)
                if self.verbose:
                    print(f"  Rate limited, retrying in {wait:.0f}s…")
                time.sleep(wait)
                self._last_call_time = time.time()
            except anthropic.APIError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF)
                continue
        else:
            raise APIError(f"API call failed after {MAX_RETRIES} retries: {last_error}")

        # Parse response
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()

        # If truncated, try to repair the JSON
        if truncated:
            text = _repair_truncated_json(text)

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

        self._pace()
        response = self._client.messages.create(
            model=self.model_id,
            max_tokens=1024,
            system=system_parts,
            messages=messages,
        )
        self._last_call_time = time.time()

        usage = response.usage
        self.usage.add(
            input_t=usage.input_tokens,
            output_t=usage.output_tokens,
            cache_write=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            cache_read=getattr(usage, "cache_read_input_tokens", 0) or 0,
        )

        return response.content[0].text
