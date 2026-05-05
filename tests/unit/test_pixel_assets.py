"""Unit tests for pixel asset resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from git_dungeon.ui_pixel.resources import candidate_asset_roots, resolve_asset_root


def test_asset_root_honors_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "manifest_sprites.json").write_text('{"sprites": {}}', encoding="utf-8")
    monkeypatch.setenv("GIT_DUNGEON_ASSET_DIR", str(tmp_path))

    assert resolve_asset_root() == tmp_path
    assert candidate_asset_roots()[0] == tmp_path


def test_bad_env_asset_root_is_explicit_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("GIT_DUNGEON_ASSET_DIR", str(tmp_path))

    with pytest.raises(FileNotFoundError, match="GIT_DUNGEON_ASSET_DIR"):
        resolve_asset_root()


def test_asset_roots_include_installed_data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("GIT_DUNGEON_ASSET_DIR", raising=False)
    monkeypatch.setattr("sys.prefix", str(tmp_path))

    assert tmp_path / "git_dungeon" / "assets" in candidate_asset_roots()
