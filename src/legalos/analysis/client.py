"""LLM provider clients with prompt caching, retries, and structured output."""

from __future__ import annotations

import json
import re
import time
from typing import TypeVar, Type

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


def _extract_json(text: str) -> str:
    """Strip markdown code fences and whitespace from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3].strip()
    return text


def _build_user_content(user_prompt: str, response_model: Type[T]) -> str:
    """Build the user message with JSON schema instructions."""
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

    return (
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


# ── Anthropic Client ─────────────────────────────────────────────


class AnthropicClient:
    """Wraps the Anthropic SDK with prompt caching and structured output."""

    def __init__(self, model_id: str, verbose: bool = False) -> None:
        import anthropic

        self.model_id = model_id
        self.verbose = verbose
        self.usage = TokenUsage()
        self._client = anthropic.Anthropic(
            api_key=get_api_key("anthropic"),
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
        """Run an analysis call with prompt caching and structured output."""
        import anthropic

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

        user_content = _build_user_content(user_prompt, response_model)

        last_error: Exception | None = None
        truncated = False
        response = None
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

                truncated = response.stop_reason == "max_tokens"
                if truncated and self.verbose:
                    print("  Output truncated — attempting to repair partial JSON…")

                break

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
        text = _extract_json(response.content[0].text)
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


# Backwards-compatible alias
AnalysisClient = AnthropicClient


# ── OpenAI Client ────────────────────────────────────────────────


class OpenAIClient:
    """Wraps the OpenAI SDK with the same .analyze()/.chat() interface."""

    def __init__(self, model_id: str, verbose: bool = False) -> None:
        try:
            import openai
        except ImportError:
            raise ImportError(
                "OpenAI support requires the openai package.\n"
                "Install it with: pip install -e \".[openai]\""
            )

        self.model_id = model_id
        self.verbose = verbose
        self.usage = TokenUsage()
        self._client = openai.OpenAI(api_key=get_api_key("openai"))
        self._last_call_time: float = 0.0
        self._call_interval: float = 0.0  # OpenAI handles rate limits via headers

    def _pace(self) -> None:
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
        import openai

        system_content = system_prompt
        if document_text:
            system_content += f"\n\n<document>\n{document_text}\n</document>"

        user_content = _build_user_content(user_prompt, response_model)

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]

        last_error: Exception | None = None
        response = None
        for attempt in range(MAX_RETRIES):
            self._pace()
            try:
                response = self._client.chat.completions.create(
                    model=self.model_id,
                    max_tokens=max_tokens,
                    messages=messages,
                    response_format={"type": "json_object"},
                )
                self._last_call_time = time.time()

                # Track token usage
                u = response.usage
                if u:
                    self.usage.add(
                        input_t=u.prompt_tokens or 0,
                        output_t=u.completion_tokens or 0,
                    )

                break

            except openai.RateLimitError as e:
                last_error = e
                wait = min(RETRY_BACKOFF * (2 ** attempt), MAX_BACKOFF)
                if self.verbose:
                    print(f"  Rate limited, retrying in {wait:.0f}s…")
                time.sleep(wait)
                self._last_call_time = time.time()
            except openai.APIError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF)
                continue
        else:
            raise APIError(f"API call failed after {MAX_RETRIES} retries: {last_error}")

        text = _extract_json(response.choices[0].message.content or "")

        # OpenAI JSON mode should return valid JSON, but repair just in case
        truncated = response.choices[0].finish_reason == "length"
        if truncated:
            if self.verbose:
                print("  Output truncated — attempting to repair partial JSON…")
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
        system_content = system_prompt
        if document_text:
            system_content += f"\n\n<document>\n{document_text}\n</document>"

        oai_messages = [{"role": "system", "content": system_content}]
        for msg in messages:
            oai_messages.append({"role": msg["role"], "content": msg["content"]})

        self._pace()
        response = self._client.chat.completions.create(
            model=self.model_id,
            max_tokens=1024,
            messages=oai_messages,
        )
        self._last_call_time = time.time()

        u = response.usage
        if u:
            self.usage.add(
                input_t=u.prompt_tokens or 0,
                output_t=u.completion_tokens or 0,
            )

        return response.choices[0].message.content or ""


# ── Google Gemini Client ─────────────────────────────────────────


class GeminiClient:
    """Wraps the Google GenAI SDK with the same .analyze()/.chat() interface."""

    def __init__(self, model_id: str, verbose: bool = False) -> None:
        try:
            from google import genai
        except ImportError:
            raise ImportError(
                "Google Gemini support requires the google-genai package.\n"
                "Install it with: pip install -e \".[google]\""
            )

        self.model_id = model_id
        self.verbose = verbose
        self.usage = TokenUsage()
        self._client = genai.Client(api_key=get_api_key("google"))
        self._last_call_time: float = 0.0
        self._call_interval: float = 0.0

    def _pace(self) -> None:
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
        from google import genai
        from google.genai import types

        system_content = system_prompt
        if document_text:
            system_content += f"\n\n<document>\n{document_text}\n</document>"

        user_content = _build_user_content(user_prompt, response_model)

        last_error: Exception | None = None
        response = None
        for attempt in range(MAX_RETRIES):
            self._pace()
            try:
                response = self._client.models.generate_content(
                    model=self.model_id,
                    contents=user_content,
                    config=types.GenerateContentConfig(
                        system_instruction=system_content,
                        max_output_tokens=max_tokens,
                        response_mime_type="application/json",
                    ),
                )
                self._last_call_time = time.time()

                # Track token usage
                u = response.usage_metadata
                if u:
                    self.usage.add(
                        input_t=u.prompt_token_count or 0,
                        output_t=u.candidates_token_count or 0,
                    )

                break

            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    wait = min(RETRY_BACKOFF * (2 ** attempt), MAX_BACKOFF)
                    if self.verbose:
                        print(f"  Error: {e}, retrying in {wait:.0f}s…")
                    time.sleep(wait)
                    self._last_call_time = time.time()
                continue
        else:
            raise APIError(f"API call failed after {MAX_RETRIES} retries: {last_error}")

        text = _extract_json(response.text or "")

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
        from google.genai import types

        system_content = system_prompt
        if document_text:
            system_content += f"\n\n<document>\n{document_text}\n</document>"

        # Convert messages to Gemini format — combine into a single prompt
        parts: list[str] = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                parts.append(f"User: {content}")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")
        prompt = "\n\n".join(parts)

        self._pace()
        response = self._client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_content,
                max_output_tokens=1024,
            ),
        )
        self._last_call_time = time.time()

        u = response.usage_metadata
        if u:
            self.usage.add(
                input_t=u.prompt_token_count or 0,
                output_t=u.candidates_token_count or 0,
            )

        return response.text or ""


# ── Factory ──────────────────────────────────────────────────────


def create_client(
    provider: str,
    model_id: str,
    verbose: bool = False,
) -> AnthropicClient | OpenAIClient | GeminiClient:
    """Create the right client class based on provider string."""
    provider = provider.lower()
    if provider == "anthropic":
        return AnthropicClient(model_id=model_id, verbose=verbose)
    elif provider == "openai":
        return OpenAIClient(model_id=model_id, verbose=verbose)
    elif provider == "google":
        return GeminiClient(model_id=model_id, verbose=verbose)
    else:
        raise ValueError(f"Unknown provider '{provider}'. Choose from: anthropic, openai, google")
