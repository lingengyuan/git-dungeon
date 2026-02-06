#!/usr/bin/env bash

set -euo pipefail

GAME_CMD="${1:-git-dungeon}"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

REPO_DIR="$WORK_DIR/smoke-repo"
METRICS_FILE="$WORK_DIR/run_metrics.json"
RUN_LOG="$WORK_DIR/run.log"

mkdir -p "$REPO_DIR"
cd "$REPO_DIR"

git init -q
git config user.name "Smoke Bot"
git config user.email "smoke@example.com"

echo "line-1" > file.txt
git add file.txt
git commit -q -m "feat: smoke init"

echo "line-2" >> file.txt
git add file.txt
git commit -q -m "fix: smoke patch"

echo "line-3" >> file.txt
git add file.txt
git commit -q -m "docs: smoke note"

set +e
"$GAME_CMD" "$REPO_DIR" --seed 42 --auto --compact --metrics-out "$METRICS_FILE" > "$RUN_LOG" 2>&1
status=$?
set -e

if [[ "$status" -ne 0 && "$status" -ne 1 ]]; then
    echo "Smoke demo failed with unexpected exit code: $status"
    cat "$RUN_LOG"
    exit "$status"
fi

if [[ ! -s "$METRICS_FILE" ]]; then
    echo "Smoke demo did not produce metrics JSON."
    cat "$RUN_LOG"
    exit 1
fi

grep -q '"battles_total"' "$METRICS_FILE"
grep -Eq 'Loading repository|Loaded [0-9]+ commits' "$RUN_LOG"

echo "Smoke demo passed (exit=$status)."
