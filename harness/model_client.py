from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class OpenAICompatibleClient:
    base_url: str
    api_key: str
    model_name: str
    timeout_seconds: int = 60
    max_retries: int = 2

    def _normalize_content(self, content: str) -> str:
        text = content.strip()
        if text.startswith("```") and text.endswith("```"):
            text = text.strip("`").strip()
            if text.startswith("json"):
                text = text[4:].strip()
        return text

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        url = self.base_url.rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                    data = json.loads(response.read().decode("utf-8"))
                choices = data.get("choices", [])
                if not choices:
                    return ""
                message = choices[0].get("message", {})
                return self._normalize_content(str(message.get("content", "")))
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt > self.max_retries:
                    break
                time.sleep(0.5 * attempt)

        raise RuntimeError(f"Model request failed after retries: {last_error}")
