# Pixel BGM Usage

Phase 17 对 BGM 做了一次试听和响度复查，目标是让标题、章节、Boss、结算之间切换时音量不突兀。运行时代码仍只使用 `src/git_dungeon/ui_pixel/audio.py` 里的槽位，不在界面显示普通音频调试文字。

## Runtime Slots

| Slot | Screen | Loop | Runtime path |
|---|---|---:|---|
| `title` | TitleScreen | yes | `assets/audio/bgm/title.ogg` |
| `chapter` | DungeonScreen | yes | `assets/audio/bgm/chapter.ogg` |
| `boss` | Reserved for boss-specific routing | yes | `assets/audio/bgm/boss.ogg` |
| `gameover` | GameOverScreen | no | `assets/audio/bgm/gameover.ogg` |

## Phase 17 Loudness Pass

Command shape:

```bash
ffmpeg -hide_banner -nostats -i <file> -filter:a volumedetect -f null /dev/null
```

After normalization:

| Slot | Mean volume | Max volume | Phase 17 processing |
|---|---:|---:|---|
| `title` | -15.0 dB | -1.8 dB | `volume=-2dB` |
| `chapter` | -14.7 dB | -7.6 dB | `volume=7.5dB` |
| `boss` | -16.0 dB | -0.6 dB | `volume=3.5dB` |
| `gameover` | -16.0 dB | -1.1 dB | `volume=-1.5dB` |

The available ffmpeg on this machine does not include `libvorbis`; use the built-in `vorbis` encoder with `-strict -2` if these files need to be regenerated.
