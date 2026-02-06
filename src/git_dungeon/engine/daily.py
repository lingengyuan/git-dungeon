"""Daily challenge helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
from typing import Iterable, Optional


@dataclass(frozen=True)
class DailyChallengeInfo:
    """Resolved daily challenge metadata."""

    date_iso: str
    seed: int


def parse_daily_date(value: Optional[str]) -> date:
    """Parse YYYY-MM-DD, defaulting to current local date when omitted."""
    if not value:
        return date.today()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Invalid --daily-date '{value}', expected YYYY-MM-DD") from exc


def daily_seed_for_date(target_date: date) -> int:
    """Use YYYYMMDD integer as deterministic daily seed."""
    return int(target_date.strftime("%Y%m%d"))


def resolve_run_seed(
    *,
    seed: Optional[int],
    daily: bool,
    daily_date: Optional[str],
) -> tuple[Optional[int], Optional[DailyChallengeInfo]]:
    """Resolve effective seed and daily metadata."""
    if not daily:
        return seed, None
    target_date = parse_daily_date(daily_date)
    resolved_seed = daily_seed_for_date(target_date)
    return resolved_seed, DailyChallengeInfo(date_iso=target_date.isoformat(), seed=resolved_seed)


def build_shareable_run_id(
    *,
    repository: str,
    seed: int,
    mutator: str,
    content_pack_ids: Iterable[str],
    daily_date_iso: Optional[str] = None,
) -> str:
    """Build deterministic shareable run id."""
    stable_packs = ",".join(sorted(content_pack_ids))
    raw = f"{repository}|{seed}|{mutator}|{stable_packs}|{daily_date_iso or '-'}"
    digest = hashlib.blake2s(raw.encode("utf-8"), digest_size=6).hexdigest()
    if daily_date_iso:
        prefix = f"daily-{daily_date_iso.replace('-', '')}"
    else:
        prefix = "run"
    return f"{prefix}-{digest}"
