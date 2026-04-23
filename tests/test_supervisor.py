from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

from app.config import AppConfig
from app.state import SupervisorState
from app.supervisor import Supervisor
from harness.result_types import HarnessRunRequest, HarnessRunResult


@dataclass
class FakeRunner:
    calls: list[HarnessRunRequest]

    def run(self, request: HarnessRunRequest) -> HarnessRunResult:
        self.calls.append(request)
        return HarnessRunResult(status="success", message="ok")


class SupervisorTests(unittest.TestCase):
    def _mk_repo(self, root: Path, name: str, rows: list[dict[str, str]] | None) -> Path:
        repo = root / name
        repo.mkdir(parents=True)
        (repo / ".git").mkdir()
        if rows is not None:
            queue_dir = repo / "queue"
            queue_dir.mkdir()
            with (queue_dir / "queue.csv").open("w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=["id", "summary", "status", "depends_on"])
                writer.writeheader()
                writer.writerows(rows)
        return repo

    def test_repo_rotation_order_and_single_item_per_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_a = self._mk_repo(root, "a", [{"id": "A1", "summary": "one", "status": "open", "depends_on": ""}])
            repo_b = self._mk_repo(root, "b", [{"id": "B1", "summary": "two", "status": "open", "depends_on": ""}])
            runner = FakeRunner(calls=[])
            supervisor = Supervisor(
                repos=[repo_a, repo_b],
                config=AppConfig(sleep_seconds=1),
                runner=runner,
                state=SupervisorState(),
                sleep_fn=lambda _s: None,
            )

            supervisor.run(one_pass=True)

            self.assertEqual([c.repo_path for c in runner.calls], [repo_a, repo_b])
            self.assertEqual([c.queue_item["id"] for c in runner.calls], ["A1", "B1"])

    def test_empty_pass_sleeps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._mk_repo(root, "a", [{"id": "A1", "summary": "one", "status": "done", "depends_on": ""}])
            sleeps: list[float] = []
            runner = FakeRunner(calls=[])

            def fake_sleep(seconds: float) -> None:
                sleeps.append(seconds)
                raise RuntimeError("stop-loop")

            supervisor = Supervisor(
                repos=[repo],
                config=AppConfig(sleep_seconds=7),
                runner=runner,
                state=SupervisorState(),
                sleep_fn=fake_sleep,
            )

            with self.assertRaisesRegex(RuntimeError, "stop-loop"):
                supervisor.run(one_pass=False)

            self.assertEqual(runner.calls, [])
            self.assertEqual(sleeps, [7])

    def test_missing_queue_artifacts_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._mk_repo(root, "a", rows=None)
            runner = FakeRunner(calls=[])
            supervisor = Supervisor(
                repos=[repo],
                config=AppConfig(sleep_seconds=1),
                runner=runner,
                state=SupervisorState(),
                sleep_fn=lambda _s: None,
            )

            supervisor.run(one_pass=True)
            self.assertEqual(runner.calls, [])

    def test_lock_lifecycle_and_state_cleared(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._mk_repo(root, "a", [{"id": "A1", "summary": "one", "status": "open", "depends_on": ""}])
            runner = FakeRunner(calls=[])
            supervisor = Supervisor(
                repos=[repo],
                config=AppConfig(sleep_seconds=1),
                runner=runner,
                state=SupervisorState(),
                sleep_fn=lambda _s: None,
            )

            supervisor.run(one_pass=True)

            self.assertFalse((repo / "queue" / "queue.lock").exists())
            self.assertFalse(supervisor.state.is_active)

    def test_single_active_run_enforced(self) -> None:
        state = SupervisorState()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state.activate(repo, "Q1", started_at=datetime.utcnow())
            with self.assertRaises(RuntimeError):
                state.activate(repo, "Q2", started_at=datetime.utcnow())


class LockFilePayloadTests(unittest.TestCase):
    def test_payload_shape(self) -> None:
        from app.locks import clear_lock, lock_path, write_lock

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "queue").mkdir()
            write_lock(repo, "Q77")
            payload = json.loads(lock_path(repo).read_text(encoding="utf-8"))
            self.assertEqual(payload["queue_id"], "Q77")
            self.assertEqual(payload["status"], "running")
            clear_lock(repo)
            self.assertFalse(lock_path(repo).exists())


if __name__ == "__main__":
    unittest.main()

class ImmediateRerunTests(unittest.TestCase):
    def test_non_empty_pass_reruns_without_sleep(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "a"
            repo.mkdir(parents=True)
            (repo / ".git").mkdir()
            q = repo / "queue"
            q.mkdir()
            with (q / "queue.csv").open("w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=["id", "summary", "status", "depends_on"])
                writer.writeheader()
                writer.writerow({"id": "A1", "summary": "one", "status": "open", "depends_on": ""})

            calls = 0

            class StopRunner(FakeRunner):
                def run(self, request: HarnessRunRequest) -> HarnessRunResult:
                    nonlocal calls
                    calls += 1
                    if calls >= 2:
                        raise RuntimeError("stop-loop")
                    return super().run(request)

            sleeps: list[float] = []
            runner = StopRunner(calls=[])
            supervisor = Supervisor(
                repos=[repo],
                config=AppConfig(sleep_seconds=5),
                runner=runner,
                state=SupervisorState(),
                sleep_fn=lambda s: sleeps.append(s),
            )

            with self.assertRaisesRegex(RuntimeError, "stop-loop"):
                supervisor.run(one_pass=False)

            self.assertEqual(sleeps, [])
            self.assertGreaterEqual(calls, 2)
