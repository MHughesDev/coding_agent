from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from app.queue_selector import select_next_item, select_next_item_with_report


class QueueSelectorPhase1Tests(unittest.TestCase):
    def _write_queue(self, root: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> Path:
        queue_csv = root / "queue.csv"
        with queue_csv.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return queue_csv

    def test_status_normalization_and_row_order_tiebreak(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue_csv = self._write_queue(
                Path(tmp),
                ["id", "summary", "status", "depends_on"],
                [
                    {"id": "A1", "summary": "first", "status": "  ToDo ", "depends_on": ""},
                    {"id": "A2", "summary": "second", "status": "ready", "depends_on": ""},
                ],
            )

            item = select_next_item(queue_csv)
            self.assertIsNotNone(item)
            self.assertEqual(item.queue_id, "A1")
            self.assertEqual(item.status, "open")

    def test_dependencies_accept_mixed_separators(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue_csv = self._write_queue(
                Path(tmp),
                ["id", "summary", "status", "depends_on"],
                [
                    {"id": "D1", "summary": "done", "status": "done", "depends_on": ""},
                    {"id": "D2", "summary": "done", "status": "completed", "depends_on": ""},
                    {"id": "A1", "summary": "target", "status": "open", "depends_on": "D1; D2\n"},
                ],
            )

            item = select_next_item(queue_csv)
            self.assertIsNotNone(item)
            self.assertEqual(item.queue_id, "A1")

    def test_duplicate_id_is_warned_and_first_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue_csv = self._write_queue(
                Path(tmp),
                ["id", "summary", "status", "depends_on"],
                [
                    {"id": "A1", "summary": "first", "status": "open", "depends_on": ""},
                    {"id": "A1", "summary": "duplicate", "status": "open", "depends_on": ""},
                ],
            )

            result = select_next_item_with_report(queue_csv)
            self.assertIsNotNone(result.item)
            self.assertEqual(result.item.summary, "first")
            self.assertTrue(any("Duplicate id" in f.message for f in result.findings))

    def test_missing_required_columns_is_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue_csv = self._write_queue(
                Path(tmp),
                ["id", "summary", "depends_on"],
                [{"id": "A1", "summary": "first", "depends_on": ""}],
            )

            result = select_next_item_with_report(queue_csv)
            self.assertIsNone(result.item)
            self.assertTrue(any(f.severity == "fatal" and f.column == "status" for f in result.findings))

    def test_unresolved_dependency_and_cycle_block_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue_csv = self._write_queue(
                Path(tmp),
                ["id", "summary", "status", "depends_on"],
                [
                    {"id": "A1", "summary": "first", "status": "open", "depends_on": "MISSING"},
                    {"id": "B1", "summary": "second", "status": "open", "depends_on": "B2"},
                    {"id": "B2", "summary": "third", "status": "open", "depends_on": "B1"},
                ],
            )

            result = select_next_item_with_report(queue_csv)
            self.assertIsNone(result.item)
            self.assertTrue(any("cannot be resolved" in f.message for f in result.findings))
            self.assertTrue(any("cycle" in f.message.lower() for f in result.findings))


if __name__ == "__main__":
    unittest.main()
