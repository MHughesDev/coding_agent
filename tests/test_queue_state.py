from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from app.queue_state import mark_item_in_progress, mark_item_terminal


class QueueStateTests(unittest.TestCase):
    def _write_queue(self, queue_csv: Path) -> None:
        with queue_csv.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["id", "summary", "status", "depends_on"])
            writer.writeheader()
            writer.writerow({"id": "A1", "summary": "work", "status": "open", "depends_on": ""})

    def test_in_progress_and_terminal_updates_are_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue_csv = Path(tmp) / "queue.csv"
            self._write_queue(queue_csv)

            updated = mark_item_in_progress(queue_csv, queue_id="A1", run_id="run-1")
            self.assertTrue(updated)
            updated = mark_item_terminal(queue_csv, queue_id="A1", terminal_status="done", run_id="run-1")
            self.assertTrue(updated)

            with queue_csv.open("r", encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))

            self.assertEqual(rows[0]["status"], "done")
            self.assertEqual(rows[0]["run_id"], "run-1")
            self.assertEqual(rows[0]["attempt_count"], "1")
            self.assertIn("updated_at", rows[0])

    def test_invalid_terminal_status_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue_csv = Path(tmp) / "queue.csv"
            self._write_queue(queue_csv)

            with self.assertRaises(ValueError):
                mark_item_terminal(queue_csv, queue_id="A1", terminal_status="unknown", run_id="run-1")


if __name__ == "__main__":
    unittest.main()
