"""Layer 3: an LLM reviewer over any OpenAI-compatible chat server (Ollama, LM Studio,
llama.cpp, or cloud providers with the user's key). Standard library only.
"""

from __future__ import annotations

import contextlib
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from legendaria_engine import paths
from legendaria_engine.config import deep_merge, read_json


class LLMError(RuntimeError):
    """The LLM server is unreachable, refused the request, or answered nonsense."""


@dataclass
class LLMSettings:
    """Where and how to call the reviewer model."""

    provider: str
    base_url: str
    model: str
    api_key: str = ""
    timeout_s: float = 180
    local: bool = True


def load_providers() -> dict[str, dict[str, Any]]:
    """Shipped provider presets plus the user's `<config dir>/providers.json`."""
    providers = read_json(paths.defaults_dir() / "providers.json")["providers"]
    user_file = paths.config_dir() / "providers.json"
    if user_file.is_file():
        providers = deep_merge(providers, read_json(user_file).get("providers", {}))
    return providers


def resolve(llm_config: dict[str, Any], **overrides: Any) -> LLMSettings:
    """Settings from config `review.llm` plus overrides (provider, base_url, model)."""
    cfg = {**llm_config, **{k: v for k, v in overrides.items() if v}}
    providers = load_providers()
    name = cfg.get("provider") or "ollama"
    if name not in providers and not cfg.get("base_url"):
        raise LLMError(f"Unknown LLM provider '{name}'. Available: {', '.join(providers)}")
    preset = providers.get(name, {})
    key_env = cfg.get("api_key_env") or preset.get("api_key_env", "")
    return LLMSettings(
        provider=name,
        base_url=(cfg.get("base_url") or preset.get("base_url", "")).rstrip("/"),
        model=cfg.get("model", ""),
        api_key=os.environ.get(key_env, "") if key_env else "",
        timeout_s=float(cfg.get("timeout_s", 180)),
        local=bool(preset.get("local", True)),
    )


class LLMClient:
    """Minimal chat-completions client."""

    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings

    def _request(self, path: str, body: dict | None = None, timeout: float | None = None) -> dict:
        url = f"{self.settings.base_url}/{path.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            url, data=data, headers=headers, method="POST" if data else "GET"
        )
        try:
            with urllib.request.urlopen(
                request, timeout=timeout or self.settings.timeout_s
            ) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise LLMError(f"{self.settings.provider} answered HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise LLMError(
                f"Cannot reach {self.settings.provider} at {self.settings.base_url}: {exc}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise LLMError(f"{self.settings.provider} sent invalid JSON") from exc

    def list_models(self) -> list[str]:
        """Model ids the server offers (`GET /models`)."""
        data = self._request("models", timeout=10)
        return [m.get("id", "") for m in data.get("data", []) if m.get("id")]

    def pick_model(self) -> str:
        """The configured model, or the first chat model the server lists."""
        if self.settings.model:
            return self.settings.model
        chat = [m for m in self.list_models() if "embed" not in m.lower()]
        if not chat:
            raise LLMError(f"No chat model available on {self.settings.provider}")
        self.settings.model = chat[0]
        return chat[0]

    def chat_json(self, prompt: str) -> dict:
        """Send one user message and parse the JSON object in the answer."""
        body = {
            "model": self.pick_model(),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        try:
            data = self._request("chat/completions", body)
        except LLMError as exc:
            if "HTTP 400" not in str(exc):
                raise
            body.pop("response_format")  # some servers do not support JSON mode
            data = self._request("chat/completions", body)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected answer from {self.settings.provider}") from exc
        return parse_json_object(content)

    def unload(self) -> None:
        """Ollama only: free the model from GPU memory now (it would stay for 5 minutes)."""
        if self.settings.provider != "ollama" or not self.settings.model:
            return
        native = self.settings.base_url.removesuffix("/v1")
        body = json.dumps({"model": self.settings.model, "keep_alive": 0}).encode()
        request = urllib.request.Request(
            f"{native}/api/generate", data=body, headers={"Content-Type": "application/json"}
        )
        with contextlib.suppress(urllib.error.URLError, OSError):
            urllib.request.urlopen(request, timeout=10).read()


def parse_json_object(text: str) -> dict:
    """The JSON object in a model answer, tolerating code fences or text around it."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise LLMError("The model did not answer with JSON")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError("The model answered with invalid JSON") from exc
