"""Synthetic repository generation for reproducible performance tests."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SyntheticRepoSpec:
    """Synthetic dataset parameters."""

    commit_count: int
    file_count: int = 48
    seed: int = 2026


def ensure_synthetic_repo(base_dir: Path, name: str, spec: SyntheticRepoSpec) -> Path:
    """Create or reuse a deterministic synthetic git repository."""
    repo_dir = base_dir / name
    metadata_path = repo_dir / ".bench_metadata.json"

    if repo_dir.exists() and metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            metadata = {}
        if (
            metadata.get("commit_count") == spec.commit_count
            and metadata.get("file_count") == spec.file_count
            and metadata.get("seed") == spec.seed
        ):
            return repo_dir

    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.mkdir(parents=True, exist_ok=True)

    _run_git(["init", "."], cwd=repo_dir)
    _run_git(["config", "user.email", "bench@example.com"], cwd=repo_dir)
    _run_git(["config", "user.name", "Bench Bot"], cwd=repo_dir)

    stream_path = repo_dir / "import.fast"
    _write_fast_import_stream(stream_path, spec)

    with stream_path.open("rb") as input_stream:
        subprocess.run(
            ["git", "fast-import", "--quiet"],
            cwd=repo_dir,
            stdin=input_stream,
            check=True,
            capture_output=True,
        )

    _run_git(["symbolic-ref", "HEAD", "refs/heads/main"], cwd=repo_dir)
    _run_git(["reset", "--hard", "--quiet", "main"], cwd=repo_dir)
    stream_path.unlink(missing_ok=True)

    metadata_path.write_text(
        json.dumps(
            {
                "commit_count": spec.commit_count,
                "file_count": spec.file_count,
                "seed": spec.seed,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return repo_dir


def count_commits(repo_path: Path) -> int:
    """Count commits in a repository quickly."""
    result = _run_git(["rev-list", "--count", "HEAD"], cwd=repo_path)
    return int(result.stdout.strip())


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _write_fast_import_stream(path: Path, spec: SyntheticRepoSpec) -> None:
    prefixes = [
        "feat",
        "fix",
        "docs",
        "refactor",
        "chore",
        "merge",
    ]
    base_timestamp = 1_700_000_000
    commit_mark_offset = spec.commit_count + 1
    previous_commit_mark: int | None = None

    with path.open("w", encoding="utf-8") as stream:
        for index in range(spec.commit_count):
            blob_mark = index + 1
            commit_mark = commit_mark_offset + index
            commit_type = prefixes[index % len(prefixes)]
            file_path = f"src/module_{index % spec.file_count:03}.txt"
            payload = (
                f"{commit_type} synthetic payload {index} seed={spec.seed} "
                f"bucket={index % spec.file_count}\n"
            )
            message = f"{commit_type}: synthetic commit {index}"
            ts = base_timestamp + index

            stream.write("blob\n")
            stream.write(f"mark :{blob_mark}\n")
            stream.write(f"data {len(payload.encode('utf-8'))}\n")
            stream.write(payload)
            stream.write("\n")

            stream.write("commit refs/heads/main\n")
            stream.write(f"mark :{commit_mark}\n")
            stream.write(f"author Bench Bot <bench@example.com> {ts} +0000\n")
            stream.write(f"committer Bench Bot <bench@example.com> {ts} +0000\n")
            stream.write(f"data {len(message.encode('utf-8'))}\n")
            stream.write(f"{message}\n")
            if previous_commit_mark is not None:
                stream.write(f"from :{previous_commit_mark}\n")
            stream.write(f"M 100644 :{blob_mark} {file_path}\n")
            stream.write("\n")
            previous_commit_mark = commit_mark

