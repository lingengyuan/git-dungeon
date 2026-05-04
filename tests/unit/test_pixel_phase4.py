"""Phase 4 tests for pixel art/audio wiring."""

from __future__ import annotations

from pathlib import Path

from git_dungeon.ui_pixel.audio import BGM_FILES, SFX_FILES, AudioManager


class _FakeMusic:
    def __init__(self) -> None:
        self.loaded: str | None = None
        self.played = False

    def load(self, path: str) -> None:
        self.loaded = path

    def set_volume(self, volume: float) -> None:
        self.volume = volume

    def play(self, loops: int) -> None:
        self.loops = loops
        self.played = True

    def stop(self) -> None:
        self.played = False


class _FakeSound:
    def __init__(self, path: str) -> None:
        self.path = path
        self.played = False

    def play(self) -> None:
        self.played = True


class _FakeMixer:
    def __init__(self, initialized: bool = True) -> None:
        self.initialized = initialized
        self.music = _FakeMusic()
        self.loaded_sounds: list[_FakeSound] = []

    def get_init(self) -> tuple[int, int, int] | None:
        if not self.initialized:
            return None
        return (44100, -16, 2)

    def Sound(self, path: str) -> _FakeSound:
        sound = _FakeSound(path)
        self.loaded_sounds.append(sound)
        return sound


class _FakePygame:
    def __init__(self, mixer: _FakeMixer) -> None:
        self.mixer = mixer


def _touch_audio_files(root: Path) -> None:
    for rel_path in [*BGM_FILES.values(), *SFX_FILES.values()]:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake ogg")


def test_audio_manager_reports_muted_when_device_unavailable(tmp_path: Path) -> None:
    audio = AudioManager(_FakePygame(_FakeMixer(initialized=False)), root=tmp_path)

    audio.load()

    status = audio.status()
    assert status.muted is True
    assert status.enabled is False
    assert "device unavailable" in status.label()


def test_audio_manager_loads_slots_and_tracks_current_bgm(tmp_path: Path) -> None:
    _touch_audio_files(tmp_path)
    mixer = _FakeMixer(initialized=True)
    audio = AudioManager(_FakePygame(mixer), root=tmp_path)

    audio.load()
    audio.play_bgm("title")
    audio.play_sfx("combat_hit")

    status = audio.status()
    assert status.enabled is True
    assert status.muted is False
    assert status.current_bgm == "title"
    assert mixer.music.played is True
    assert any(sound.played for sound in mixer.loaded_sounds)


def test_gpt_image_asset_cards_are_explicitly_pending() -> None:
    cards = Path("assets/generated/asset_cards.yml").read_text(encoding="utf-8")

    assert "source: gpt-image-2" in cards
    assert "status: pending_generation" in cards
    assert "prompt_file: assets/source_prompts/title_banner.md" in cards
