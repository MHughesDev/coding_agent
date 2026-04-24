from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from harness.result_types import HarnessRunRequest
from harness.runner import HarnessRunner


class _FakeClient:
    def __init__(self, response: str) -> None:
        self.response = response

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        _ = system_prompt
        _ = user_prompt
        return self.response


class HarnessRunnerTests(unittest.TestCase):
    def _mk_repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir(parents=True)
        (repo / "pyproject.toml").write_text("[project]\nname='demo'\nversion='0.1.0'\n", encoding="utf-8")
        (repo / "queue").mkdir()
        return repo

    def test_runner_writes_artifact_and_returns_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._mk_repo(Path(tmp))
            runner = HarnessRunner(
                model_client=_FakeClient(
                    '{"steps":[{"intent":"Add feature","acceptance":"tests pass","targets":["app/main.py"]}]}'
                )
            )
            request = HarnessRunRequest(
                repo_path=repo,
                queue_item={"id": "Q1", "summary": "demo work", "status": "open", "related_files": "app/main.py"},
            )

            result = runner.run(request)

            self.assertEqual(result.status, "success")
            self.assertIn("validation", result.message.lower())
            touched = result.metadata["touched_files"]
            self.assertTrue(touched)
            artifact = repo / touched[0]
            self.assertTrue(artifact.exists())

    def test_malformed_model_output_falls_back_to_default_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._mk_repo(Path(tmp))
            runner = HarnessRunner(model_client=_FakeClient("not-json"))
            request = HarnessRunRequest(
                repo_path=repo,
                queue_item={"id": "Q2", "summary": "fallback", "status": "open"},
            )

            result = runner.run(request)

            self.assertEqual(result.status, "success")
            self.assertTrue(result.metadata["plan_malformed_output"])
            self.assertGreaterEqual(len(result.metadata["plan_steps"]), 1)


if __name__ == "__main__":
    unittest.main()
