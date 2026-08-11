---
name: digest-video
license: MIT
description: Turn a local video into frames plus a transcript so it can be understood. Use when the user shares a video, Loom, or screen recording and wants it broken into snapshots and text.
---

Ask the user for the input video path and the output directory, then:

```bash
IN="<video>"; OUT="<dir>"; mkdir -p "$OUT/frames"
ffmpeg -i "$IN" -vf "fps=1/5" "$OUT/frames/frame_%04d.png"   # 1 frame / 5s; scene-change: -vf "select='gt(scene,0.3)'" -vsync vfr
ffmpeg -i "$IN" -vn -ar 16000 -ac 1 "$OUT/audio.wav"
command -v whisper >/dev/null || brew install openai-whisper
whisper "$OUT/audio.wav" --model base --output_format all --output_dir "$OUT"
```

Then read the frames and `$OUT/audio.txt` to understand the video.
