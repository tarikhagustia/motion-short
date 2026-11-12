#!/usr/bin/env python3
"""Make the voice-over for a motion-shorts project: OmniVoice per scene + Whisper word timings.

Usage:
    python voice.py PROJECT_DIR                 # all scenes
    python voice.py PROJECT_DIR --only s03 s07  # redo some scenes (others are reused)
    python voice.py PROJECT_DIR --speed 1.12    # pitch-preserving speed-up of the joined take
    python voice.py PROJECT_DIR --align-only    # keep the clips, just redo the word timings

Reads storyboard.json (each scene's `spoken`, falling back to `narration`). Delivery tags in
square brackets are stripped because OmniVoice does not perform them.

Writes into PROJECT_DIR/audio/:
    sNN.mp3/.wav       one clip per scene (OmniVoice)
    narration.wav      all clips joined with a short gap, optionally sped up
    vo_words.json      {"words": [{"scene", "text", "start", "end"}, ...]}  (Whisper, word level)

Then run build_timeline.py, which reads narration.wav + vo_words.json.
Needs: ffmpeg, faster-whisper (pip install faster-whisper), the OmniVoice server reachable.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TTS = HERE / "omnivoice_tts.py"
AUDIO_EXT = (".wav", ".mp3", ".m4a", ".flac")


def strip_tags(text):
    text = re.sub(r"\[[^\]]*\]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def find_clip(adir, sid):
    for e in AUDIO_EXT:
        p = adir / f"{sid}{e}"
        if p.exists():
            return p
    return None


def tts_scene(text, out_base):
    r = subprocess.run([sys.executable, str(TTS), "--text", text, "--out", str(out_base) + ".wav"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"OmniVoice failed for {out_base.name}:\n{r.stderr[-1500:]}")
    try:
        info = json.loads(r.stdout[r.stdout.index("{"):])
        return Path(info["output"]) if "output" in info else find_clip(out_base.parent, out_base.name)
    except Exception:
        return find_clip(out_base.parent, out_base.name)


def decode(path, rate=16000):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(rate), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def trim_silence(src, dst):
    """Cut leading/trailing silence so scenes join tightly."""
    af = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
          "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", af, "-ar", "48000", "-ac", "1", str(dst)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--only", nargs="*", help="scene ids to regenerate")
    ap.add_argument("--speed", type=float, default=1.0, help="atempo on the joined take (1.0-1.3)")
    ap.add_argument("--gap", type=float, default=0.28, help="pause between scenes in seconds")
    ap.add_argument("--model", default="small", help="faster-whisper model (small is fast and good for Indonesian)")
    ap.add_argument("--align-only", action="store_true")
    args = ap.parse_args()

    proj = Path(args.project).resolve()
    sb = json.loads((proj / "storyboard.json").read_text(encoding="utf-8"))
    adir = proj / "audio"
    adir.mkdir(exist_ok=True)
    cut = adir / ".trim"
    cut.mkdir(exist_ok=True)

    # 1. one OmniVoice clip per scene
    for sc in sb["scenes"]:
        sid = sc["id"]
        have = find_clip(adir, sid)
        redo = args.only is not None and sid in args.only
        if args.align_only or (have and not redo):
            continue
        if have:
            have.unlink()
        text = strip_tags(sc.get("spoken") or sc["narration"])
        print(f"tts {sid}: {text}", file=sys.stderr)
        tts_scene(text, adir / sid)

    # 2. trim + join with gaps (+ optional speed-up)
    clips = []
    for sc in sb["scenes"]:
        c = find_clip(adir, sc["id"])
        if not c:
            raise SystemExit(f"missing clip for {sc['id']}")
        t = cut / f"{sc['id']}.wav"
        trim_silence(c, t)
        clips.append(t)
    # pause after each scene: storyboard scene "gap_after" (s) for a held silence, else --gap
    gaps = [float(sc.get("gap_after", args.gap)) for sc in sb["scenes"]]
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for c in clips:
        cmd += ["-i", str(c)]
    filt = "".join(f"[{i}:a]apad=pad_dur={gaps[i] if i < len(clips) - 1 else 0.05}[p{i}];" for i in range(len(clips)))
    filt += "".join(f"[p{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=0:a=1"
    if abs(args.speed - 1.0) > 0.001:
        filt += f",atempo={args.speed:.3f}"
    filt += ",adelay=150:all=1[out]"  # tiny lead-in so the first word isn't clipped
    narration = adir / "narration.wav"
    cmd += ["-filter_complex", filt, "-map", "[out]", "-ar", "48000", "-ac", "1", str(narration)]
    subprocess.run(cmd, check=True)

    # scene boundaries in the joined file
    durs = [len(decode(c)) / 16000 for c in clips]
    starts = [0.15 + sum(durs[:i]) + sum(gaps[:i]) for i in range(len(durs))]
    starts = [0.15 + (s - 0.15) / args.speed for s in starts]

    # 3. Whisper word timings, one scene clip at a time (a single pass over a long take can skip
    #    30+ s of speech; per clip it can't, and every word lands in its own scene by construction)
    from faster_whisper import WhisperModel
    import os
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    audio = decode(narration)
    words = []
    for si, (sc, c) in enumerate(zip(sb["scenes"], clips)):
        segs, _ = model.transcribe(decode(c), language="id", word_timestamps=True,
                                   initial_prompt=strip_tags(sc.get("spoken") or sc["narration"]),
                                   vad_filter=False, condition_on_previous_text=False)
        for s in segs:
            for w in s.words:
                words.append({"scene": si, "text": w.word.strip(),
                              "start": round(starts[si] + w.start / args.speed, 3),
                              "end": round(starts[si] + w.end / args.speed, 3)})
    (adir / "vo_words.json").write_text(json.dumps({"words": words}, ensure_ascii=False, indent=1), encoding="utf-8")
    total = len(audio) / 16000
    per_scene = {sb["scenes"][i]["id"]: sum(1 for w in words if w["scene"] == i) for i in range(len(sb["scenes"]))}
    empty = [k for k, v in per_scene.items() if v == 0]
    print(json.dumps({"narration": str(narration), "duration": round(total, 2), "words": len(words),
                      "scenes_without_words": empty}, ensure_ascii=False))


if __name__ == "__main__":
    main()
