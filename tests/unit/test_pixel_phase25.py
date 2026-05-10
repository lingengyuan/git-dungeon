"""Phase 25 tests for PC release documentation state."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_pixel_phase_plan_marks_pc_line_complete() -> None:
    text = (ROOT / "plans/pixel-phases.md").read_text(encoding="utf-8")

    assert "Phase 0-25 已完成" in text
    assert "PC-only" in text
    for phase in range(19, 26):
        assert f"| Phase {phase} " in text
    assert "| Phase 25 | PC 发布前固定" in text
    assert "✅ 完成 (2026-05-10)" in text


def test_pc_release_checklist_declares_out_of_scope_inputs() -> None:
    text = (ROOT / "plans/pixel-pc-release-checklist.md").read_text(encoding="utf-8")

    assert "不支持手柄" in text
    assert "不支持移动端" in text
    assert "PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel" in text
    assert "scripts/render_pixel_screens.py" in text


def test_agents_points_next_session_to_pc_release_checklist() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "Phase 0-25 已完成" in text
    assert "plans/pixel-pc-release-checklist.md" in text
