# gameover.ogg processing notes

## Source

- 集合：[Chill Chiptunes Collection](https://opengameart.org/content/chill-chiptunes-collection) by **Holizna** (CC0 1.0)
- 原 zip：`chill_chiptunes.zip` (75.8 MB)
- 选取曲目：`05 HoliznaCC0 - Complications.ogg`（118.7s，OGG vorbis stereo）
  - 选这首的理由：曲名 "Complications" 与 game over 语境契合；旋律柔和略带忧郁；时长够提供干净的 12s 片段。

## Clip parameters

| 参数 | 值 |
|---|---|
| 起始 (`-ss`) | 8.0s |
| 长度 (`-t`) | 12.0s |
| 淡入 | 0-1s |
| 淡出 | 11-12s |
| 输出格式 | OGG vorbis stereo @128k (`-c:a vorbis -strict experimental`) |
| 输出时长 | 12.000363s |
| 输出大小 | ~64 KB |

## ffmpeg command

```bash
ffmpeg -y -hide_banner -loglevel warning \
  -i "assets/_downloads/05 HoliznaCC0 - Complications.ogg" \
  -ss 8 -t 12 \
  -af "afade=t=in:st=0:d=1,afade=t=out:st=11:d=1" \
  -ac 2 -c:a vorbis -strict experimental -b:a 128k \
  assets/audio/bgm/gameover.ogg
```

## Reproducing

1. 下载 `chill_chiptunes.zip` 到 `assets/_downloads/`（gitignored）。
2. 解压 `Chill Chiptunes/05 HoliznaCC0 - Complications.ogg` 到 `assets/_downloads/`。
3. 跑上面的 ffmpeg 命令。

## Why not libvorbis

macOS 默认 `brew install ffmpeg` 不带 `libvorbis` 编码器。改用 ffmpeg 内置的 `vorbis` 实验编码器（需要 `-strict experimental` + `-ac 2` 强制立体声）。输出文件兼容 `pygame.mixer.music.load()`。
