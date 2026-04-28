from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .base import LLMError, extract_json_object


@dataclass(slots=True)
class OpenAICompatibleClient:
    base_url: str
    api_key_env: str
    model: str
    timeout_seconds: int = 120
    max_output_tokens: int | None = None
    temperature: float | None = 0.2
    reasoning_effort: str = ""
    response_format_json: bool = True
    extra_body: dict[str, Any] | None = None

    def complete(self, prompt: str) -> str:
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise LLMError(f"Missing API key environment variable: {self.api_key_env}")
        if not self.base_url:
            raise LLMError("Missing openai_compatible.base_url")
        if not self.model:
            raise LLMError("Missing openai_compatible.model")

        endpoint = self.base_url.rstrip("/") + "/chat/completions"
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if self.temperature is not None:
            body["temperature"] = self.temperature
        if self.reasoning_effort:
            body["reasoning_effort"] = self.reasoning_effort
        if self.response_format_json:
            body["response_format"] = {"type": "json_object"}
        if self.max_output_tokens:
            body["max_tokens"] = self.max_output_tokens
        if self.extra_body:
            body.update(self.extra_body)

        request = urllib.request.Request(
            endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise LLMError(f"OpenAI-compatible API failed: HTTP {exc.code}: {body_text}") from exc
        except OSError as exc:
            raise LLMError(f"OpenAI-compatible API request failed: {exc}") from exc

        try:
            return payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("OpenAI-compatible API response did not contain message content.") from exc

    def complete_json(self, prompt: str) -> dict[str, Any]:
        return extract_json_object(self.complete(prompt))
