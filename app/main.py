from __future__ import annotations

from app.cli import parse_args
from app.config import AppConfig
from app.logging_setup import configure_logging
from app.state import SupervisorState
from app.supervisor import Supervisor
from harness.model_client import OpenAICompatibleClient
from harness.runner import HarnessRunner


def main() -> None:
    args = parse_args()
    configure_logging()
    config = AppConfig.from_env(
        default_sleep_seconds=args.sleep_seconds,
        default_lock_stale_seconds=args.lock_stale_seconds,
    )
    model_client = OpenAICompatibleClient(
        base_url=config.model_base_url,
        api_key=config.model_api_key,
        model_name=config.model_name,
    )
    supervisor = Supervisor(
        repos=args.repos,
        config=config,
        runner=HarnessRunner(model_client=model_client),
        state=SupervisorState(),
    )
    supervisor.run(one_pass=args.one_pass)


if __name__ == "__main__":
    main()
