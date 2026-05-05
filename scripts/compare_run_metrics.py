#!/usr/bin/env python3
"""Compare CLI and Pixel headless run metrics."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_FIELDS = (
    "run_victory",
    "chapters_completed",
    "battles_total",
    "boss_battles_total",
    "battles_won",
    "total_exp_gained",
    "total_gold_gained",
    "node_type_counts",
)


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    if len(args) != 2:
        print("usage: compare_run_metrics.py <cli.json> <pixel.json>", file=sys.stderr)
        return 2

    left = _read_json(Path(args[0]))
    right = _read_json(Path(args[1]))
    mismatches: list[str] = []
    for field in REQUIRED_FIELDS:
        if left.get(field) != right.get(field):
            mismatches.append(f"{field}: cli={left.get(field)!r} pixel={right.get(field)!r}")

    if mismatches:
        print("METRICS MISMATCH")
        for item in mismatches:
            print(f"- {item}")
        return 1

    print("METRICS MATCH")
    for field in REQUIRED_FIELDS:
        print(f"- {field}: {left.get(field)!r}")
    return 0


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
