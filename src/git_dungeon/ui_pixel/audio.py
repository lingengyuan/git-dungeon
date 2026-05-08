"""Audio routing for the pixel UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from git_dungeon.ui_pixel.resources import resolve_asset_root


BGM_FILES = {
    "title": "assets/audio/bgm/title.ogg",
    "chapter": "assets/audio/bgm/chapter.ogg",
    "boss": "assets/audio/bgm/boss.ogg",
    "gameover": "assets/audio/bgm/gameover.ogg",
}

BGM_LOOPS = {
    "title": -1,
    "chapter": -1,
    "boss": -1,
    "gameover": 0,
}

SFX_FILES = {
    "ui_confirm": "assets/audio/sfx/kenney_ui_audio/Audio/click1.ogg",
    "ui_cancel": "assets/audio/sfx/kenney_ui_audio/Audio/click2.ogg",
    "ui_denied": "assets/audio/sfx/kenney_ui_audio/Audio/switch10.ogg",
    "combat_hit": "assets/audio/sfx/kenney_rpg_audio/Audio/knifeSlice.ogg",
    "combat_crit": "assets/audio/sfx/kenney_rpg_audio/Audio/chop.ogg",
    "combat_hurt": "assets/audio/sfx/kenney_rpg_audio/Audio/cloth2.ogg",
    "combat_defend": "assets/audio/sfx/kenney_rpg_audio/Audio/metalClick.ogg",
    "combat_kill": "assets/audio/sfx/kenney_rpg_audio/Audio/metalPot3.ogg",
    "economy": "assets/audio/sfx/kenney_rpg_audio/Audio/handleCoins.ogg",
    "progress": "assets/audio/sfx/kenney_rpg_audio/Audio/bookFlip1.ogg",
    "event": "assets/audio/sfx/kenney_rpg_audio/Audio/bookOpen.ogg",
    "rest": "assets/audio/sfx/kenney_rpg_audio/Audio/clothBelt.ogg",
}


@dataclass(frozen=True)
class AudioStatus:
    enabled: bool
    muted: bool
    reason: str = ""
    current_bgm: str | None = None

    def label(self) -> str:
        if self.enabled and not self.muted:
            return f"Audio: {self.current_bgm or 'ready'}"
        reason = self.reason or "unavailable"
        return f"Audio muted: {reason}"


class AudioManager:
    """Small pygame mixer wrapper with explicit muted status."""

    def __init__(self, pygame_module: Any, root: Path | None = None) -> None:
        self._pygame = pygame_module
        self._asset_root = root or resolve_asset_root()
        self._sounds: dict[str, Any] = {}
        self._bgm_volume = 0.45
        self._sfx_volume = 0.70
        self._status = AudioStatus(enabled=False, muted=True, reason="not loaded")

    def load(self) -> None:
        mixer = getattr(self._pygame, "mixer", None)
        if mixer is None:
            self._status = AudioStatus(enabled=False, muted=True, reason="mixer missing")
            return
        try:
            if mixer.get_init() is None:
                self._status = AudioStatus(enabled=False, muted=True, reason="device unavailable")
                return
        except Exception as exc:
            self._status = AudioStatus(enabled=False, muted=True, reason=str(exc)[:48])
            return

        missing = self._missing_files()
        if missing:
            self._status = AudioStatus(
                enabled=False,
                muted=True,
                reason=f"missing {missing[0].name}",
            )
            return

        try:
            self._sounds = {slot: mixer.Sound(str(self._path(rel_path))) for slot, rel_path in SFX_FILES.items()}
        except Exception as exc:
            self._sounds = {}
            self._status = AudioStatus(enabled=False, muted=True, reason=str(exc)[:48])
            return

        self._status = AudioStatus(enabled=True, muted=False, reason="")

    def set_volumes(self, bgm: int, sfx: int) -> None:
        self._bgm_volume = max(0.0, min(1.0, bgm / 100))
        self._sfx_volume = max(0.0, min(1.0, sfx / 100))
        for sound in self._sounds.values():
            try:
                sound.set_volume(self._sfx_volume)
            except Exception:
                pass
        try:
            self._pygame.mixer.music.set_volume(self._bgm_volume)
        except Exception:
            pass

    def status(self) -> AudioStatus:
        return self._status

    def play_bgm(self, slot: str) -> None:
        if not self._status.enabled or self._status.muted or self._status.current_bgm == slot:
            return
        rel_path = BGM_FILES.get(slot)
        if rel_path is None:
            self._mute(f"unknown bgm {slot}")
            return
        path = self._path(rel_path)
        try:
            self._pygame.mixer.music.load(str(path))
            self._pygame.mixer.music.set_volume(self._bgm_volume)
            self._pygame.mixer.music.play(BGM_LOOPS[slot])
        except Exception as exc:
            self._mute(str(exc)[:48])
            return
        self._status = AudioStatus(enabled=True, muted=False, current_bgm=slot)

    def play_sfx(self, slot: str) -> None:
        if not self._status.enabled or self._status.muted:
            return
        sound = self._sounds.get(slot)
        if sound is None:
            self._mute(f"unknown sfx {slot}")
            return
        try:
            sound.play()
        except Exception as exc:
            self._mute(str(exc)[:48])

    def stop_bgm(self) -> None:
        if not self._status.enabled:
            return
        try:
            self._pygame.mixer.music.stop()
        except Exception as exc:
            self._mute(str(exc)[:48])
            return
        self._status = AudioStatus(enabled=True, muted=False)

    def _missing_files(self) -> list[Path]:
        paths = [self._path(rel_path) for rel_path in BGM_FILES.values()]
        paths.extend(self._path(rel_path) for rel_path in SFX_FILES.values())
        return [path for path in paths if not path.exists()]

    def _path(self, rel_path: str) -> Path:
        clean = rel_path.removeprefix("assets/")
        return self._asset_root / clean

    def _mute(self, reason: str) -> None:
        self._status = AudioStatus(
            enabled=False,
            muted=True,
            reason=reason or "playback failed",
            current_bgm=self._status.current_bgm,
        )
