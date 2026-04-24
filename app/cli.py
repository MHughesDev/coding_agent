from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CliArgs:
    repos: list[Path]
    sleep_seconds: int
    lock_stale_seconds: int
    one_pass: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Queue Agent Supervisor")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repo", type=Path, help="Single repository root")
    group.add_argument("--repos", nargs="+", type=Path, help="Ordered repository roots")
    parser.add_argument("--sleep-seconds", type=int, default=60, help="Sleep interval after empty full pass")
    parser.add_argument(
        "--lock-stale-seconds",
        type=int,
        default=1800,
        help="Lock age threshold (seconds) before automatic stale recovery",
    )
    parser.add_argument("--one-pass", action="store_true", help="Run exactly one full pass and exit")
    return parser


def parse_args(argv: list[str] | None = None) -> CliArgs:
    ns = build_parser().parse_args(argv)
    repos = [ns.repo] if ns.repo else list(ns.repos)
    if ns.sleep_seconds < 1:
        raise SystemExit("--sleep-seconds must be >= 1")
    if ns.lock_stale_seconds < 1:
        raise SystemExit("--lock-stale-seconds must be >= 1")
    return CliArgs(
        repos=repos,
        sleep_seconds=ns.sleep_seconds,
        lock_stale_seconds=ns.lock_stale_seconds,
        one_pass=ns.one_pass,
    )
