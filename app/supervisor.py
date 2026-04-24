from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

from app import locks, queue_state
from app.config import AppConfig
from app.scheduler import perform_full_pass
from app.state import SupervisorState
from harness.result_types import HarnessRunRequest, HarnessRunResult
from harness.runner import HarnessRunner

logger = logging.getLogger(__name__)

_RESULT_TO_QUEUE_STATUS = {
    "success": "done",
    "failed": "failed",
    "blocked": "blocked",
    "skipped": "open",
}


@dataclass
class Supervisor:
    repos: list[Path]
    config: AppConfig
    runner: HarnessRunner
    state: SupervisorState
    sleep_fn: Callable[[float], None] = time.sleep

    def run(self, one_pass: bool = False) -> None:
        pass_index = 0
        while True:
            pass_index += 1
            logger.info("Starting pass %s across %s repos", pass_index, len(self.repos))
            pass_result = perform_full_pass(self.repos)
            had_work = False

            for work in pass_result.works:
                repo = work.scan.repo_path
                if not work.scan.looks_like_repo:
                    logger.warning("Skipping invalid repo root: %s", repo)
                    continue
                recovery = locks.recover_lock_if_needed(
                    repo_path=repo,
                    queue_csv=work.scan.queue_csv,
                    stale_after_seconds=self.config.lock_stale_seconds,
                )
                if recovery.should_skip_repo or recovery.lock_cleared:
                    continue

                if work.item is None or work.scan.queue_csv is None:
                    logger.info("Repo %s has no actionable queue item", repo)
                    continue

                had_work = True
                started = datetime.now(timezone.utc)
                run_id = f"run-{uuid4()}"
                queue_id = work.item.queue_id
                queue_state.mark_item_in_progress(
                    queue_csv=work.scan.queue_csv,
                    queue_id=queue_id,
                    run_id=run_id,
                    started_at=started,
                )
                self.state.activate(repo=repo, queue_id=queue_id, started_at=started)
                locks.write_lock(repo, queue_id, run_id=run_id, pass_index=pass_index)
                try:
                    request = HarnessRunRequest(repo_path=repo, queue_item=work.item.raw)
                    result = self.runner.run(request)
                    self._log_result(repo, queue_id, result)
                    queue_state.mark_item_terminal(
                        queue_csv=work.scan.queue_csv,
                        queue_id=queue_id,
                        terminal_status=_RESULT_TO_QUEUE_STATUS.get(result.status, "failed"),
                        run_id=run_id,
                        finished_at=datetime.now(timezone.utc),
                        last_error="" if result.status == "success" else result.message,
                    )
                except Exception as exc:
                    queue_state.mark_item_terminal(
                        queue_csv=work.scan.queue_csv,
                        queue_id=queue_id,
                        terminal_status="failed",
                        run_id=run_id,
                        finished_at=datetime.now(timezone.utc),
                        last_error=str(exc),
                    )
                    raise
                finally:
                    locks.clear_lock(repo)
                    self.state.clear()

            if one_pass:
                logger.info("one-pass mode complete; exiting")
                return
            if had_work:
                logger.info("Pass %s found work; starting next pass immediately", pass_index)
                continue

            logger.info(
                "Pass %s fully empty; sleeping for %s seconds",
                pass_index,
                self.config.sleep_seconds,
            )
            self.sleep_fn(self.config.sleep_seconds)

    @staticmethod
    def _log_result(repo: Path, queue_id: str, result: HarnessRunResult) -> None:
        logger.info(
            "Run finished repo=%s queue_id=%s status=%s message=%s",
            repo,
            queue_id,
            result.status,
            result.message,
        )
