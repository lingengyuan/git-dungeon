"""Unit tests for pixel audio slots."""

from __future__ import annotations

from pathlib import Path

from git_dungeon.ui_pixel.audio import BGM_FILES, SFX_FILES, AudioManager


class _NoMixerPygame:
    mixer = None


def test_audio_manager_reports_missing_mixer(tmp_path: Path) -> None:
    (tmp_path / "manifest_sprites.json").write_text('{"sprites": {}}', encoding="utf-8")
    audio = AudioManager(_NoMixerPygame(), root=tmp_path)

    audio.load()

    assert audio.status().muted is True
    assert "mixer missing" in audio.status().label()


def test_audio_slot_paths_stay_inside_assets_tree() -> None:
    for rel_path in [*BGM_FILES.values(), *SFX_FILES.values()]:
        assert rel_path.startswith("assets/")
        assert ".." not in Path(rel_path).parts
