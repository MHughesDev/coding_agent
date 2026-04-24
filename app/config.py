from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    sleep_seconds: int = 60
    lock_stale_seconds: int = 1800
    model_base_url: str = "http://localhost:11434/v1"
    model_api_key: str = ""
    model_name: str = "llama3.1"

    @staticmethod
    def from_env(default_sleep_seconds: int = 60, default_lock_stale_seconds: int = 1800) -> "AppConfig":
        return AppConfig(
            sleep_seconds=default_sleep_seconds,
            lock_stale_seconds=int(os.getenv("LOCK_STALE_SECONDS", str(default_lock_stale_seconds))),
            model_base_url=os.getenv("MODEL_BASE_URL", "http://localhost:11434/v1"),
            model_api_key=os.getenv("MODEL_API_KEY", ""),
            model_name=os.getenv("MODEL_NAME", "llama3.1"),
        )
