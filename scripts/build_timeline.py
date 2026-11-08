#!/usr/bin/env python3
"""Build timeline.json (scene times, word times, caption pages) for a fakta-shorts project.

Usage:
    python build_timeline.py PROJECT_DIR [--audio-dir PROJECT_DIR/audio] [--chars-per-sec 18]

PROJECT_DIR must contain storyboard.json. If an audio file exists for a scene
(<audio-dir>/<scene id>.wav|.mp3|.m4a), its real length sets the scene length and
the words are spread over the detected speech (pauses are matched to punctuation).
Scenes without audio get an estimated length so a silent preview can still be made.

Writes PROJECT_DIR/timeline.json and, when every scene has audio,
PROJECT_DIR/narration.wav (all scene clips joined with the scene padding).
Needs ffmpeg/ffprobe on PATH only when audio is used.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

AUDIO_EXT = (".wav", ".mp3", ".m4a", ".flac", ".ogg")
PAUSE = {",": 0.22, ";": 0.3, ":": 0.3, ".": 0.42, "?": 0.45, "!": 0.45, "…": 0.45, "—": 0.2, "–": 0.2}
DIGIT_WORDS = 3.2  # a digit is spoken as roughly this many letters ("79" -> "tujuh puluh sembilan")


def norm(w):
    return re.sub(r"[^\w±%]", "", w.lower())


def spoken_weight(word):
    core = re.sub(r"[^\w±%]", "", word)
    digits = sum(ch.isdigit() for ch in core)
    letters = len(core) - digits
    w = letters + digits * DIGIT_WORDS
    if "±" in core:
        w += 6  # "sekitar"
    if "%" in core:
        w += 6  # "persen"
    return max(w, 1.5) + 1.0  # +1 for the gap between words


def trailing_pause(word):
    for ch in reversed(word):
        if ch in PAUSE:
            return PAUSE[ch]
        if ch.isalnum():
            break
    return 0.0


def ffprobe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(out.stdout.strip())


def detect_silences(path, noise_db=-38, min_d=0.14):
    """Return list of (start, end) silences found by ffmpeg silencedetect."""
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
                        f"silencedetect=noise={noise_db}dB:d={min_d}", "-f", "null", "-"],
                       capture_output=True, text=True)
    sil, start = [], None
    for line in p.stderr.splitlines():
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m:
            start = float(m.group(1))
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and start is not None:
            sil.append((start, float(m.group(1))))
            start = None
    if start is not None:
        sil.append((start, 1e9))
    return sil


def spread(words, t0, t1):
    """Spread words over [t0, t1] by spoken weight, honouring punctuation pauses."""
    weights = [spoken_weight(w) for w in words]
    pauses = [trailing_pause(w) for w in words[:-1]] + [0.0]
    total_pause = sum(pauses)
    span = max(t1 - t0, 0.2)
    if total_pause > span * 0.35:  # squeeze pauses on very fast audio
        f = span * 0.35 / total_pause
        pauses = [p * f for p in pauses]
        total_pause = sum(pauses)
    rate = (span - total_pause) / sum(weights)
    out, t = [], t0
    for w, wt, ps in zip(words, weights, pauses):
        d = wt * rate
        out.append((t, t + d))
        t += d + ps
    return out


def time_scene_words(words, dur, audio=None):
    """Word timings inside one scene (seconds from scene start)."""
    if not audio:
        return spread(words, 0.05, dur - 0.05)
    sil = detect_silences(audio)
    speech_start = 0.0
    speech_end = dur
    if sil and sil[0][0] <= 0.02:
        speech_start = min(sil[0][1], dur * 0.4)
    if sil and sil[-1][1] >= dur - 0.02:
        speech_end = max(sil[-1][0], speech_start + 0.3)
    inner = [(a, b) for a, b in sil if a > speech_start + 0.05 and b < speech_end - 0.05]
    # phrase boundaries = words that end with punctuation (not the last word)
    bounds = [i for i, w in enumerate(words[:-1]) if trailing_pause(w) > 0]
    if bounds and len(inner) >= len(bounds):
        # keep the longest pauses, one per boundary, in time order
        chosen = sorted(sorted(inner, key=lambda s: s[1] - s[0], reverse=True)[:len(bounds)])
        out, seg_start, prev = [], speech_start, 0
        for bi, (a, b) in zip(bounds, chosen):
            seg = words[prev:bi + 1]
            out += spread(seg, seg_start, a)
            seg_start, prev = b, bi + 1
        out += spread(words[prev:], seg_start, speech_end)
        return out
    return spread(words, speech_start, speech_end)


def paginate(words, max_words=4, max_chars=24):
    """Group global word indexes into caption pages, breaking after punctuation."""
    pages, cur, chars = [], [], 0
    for i, w in enumerate(words):
        text = w["text"]
        if cur and (len(cur) >= max_words or chars + len(text) > max_chars or w["scene"] != words[cur[-1]]["scene"]):
            pages.append(cur)
            cur, chars = [], 0
        cur.append(i)
        chars += len(text) + 1
        if trailing_pause(text) >= 0.4 or (trailing_pause(text) > 0 and len(cur) >= 2):
            pages.append(cur)
            cur, chars = [], 0
    if cur:
        pages.append(cur)
    # merge a lonely trailing word into the previous page of the same scene when it fits
    merged = []
    for p in pages:
        if (merged and len(p) == 1 and len(merged[-1]) < max_words + 1
                and words[p[0]]["scene"] == words[merged[-1][-1]]["scene"]
                and trailing_pause(words[merged[-1][-1]]["text"]) < 0.4):
            merged[-1] = merged[-1] + p
        else:
            merged.append(p)
    return merged


def find_audio(audio_dir, sid):
    for ext in AUDIO_EXT:
        p = audio_dir / f"{sid}{ext}"
        if p.exists():
            return p
    return None


def timeline_from_vo(sb, vo_words, audio_len, tail, lead=0.22):
    """Scene and word times from word timings of one continuous voice-over (e.g. ElevenLabs with-timestamps).
    Caption words (narration) are matched to spoken words (spoken text, numbers written out)."""
    import difflib
    by_scene = {}
    for w in vo_words:
        by_scene.setdefault(w["scene"], []).append(w)
    words_out, firsts = [], []
    for si, sc in enumerate(sb["scenes"]):
        nar = sc["narration"].split()
        sp = by_scene.get(si, [])
        keys = {norm(k) for k in sc.get("keywords", [])}
        times = [None] * len(nar)
        if sp:
            sm = difflib.SequenceMatcher(a=[norm(w) for w in nar], b=[norm(w["text"]) for w in sp], autojunk=False)
            for op, i1, i2, j1, j2 in sm.get_opcodes():
                if op == "equal":
                    for k in range(i2 - i1):
                        times[i1 + k] = (sp[j1 + k]["start"], sp[j1 + k]["end"])
                elif op == "replace":  # e.g. "1814" <-> "delapan belas empat belas"
                    span = spread(nar[i1:i2], sp[j1]["start"], sp[j2 - 1]["end"])
                    for k, ab in enumerate(span):
                        times[i1 + k] = ab
            # words that were not spoken at all: borrow the neighbour's time
            for k in range(len(nar)):
                if times[k] is None:
                    prev = next((times[j] for j in range(k - 1, -1, -1) if times[j]), None)
                    nxt = next((times[j] for j in range(k + 1, len(nar)) if times[j]), None)
                    t0 = prev[1] if prev else (nxt[0] if nxt else 0.0)
                    times[k] = (t0, t0 + 0.05)
        else:
            raise SystemExit(f"scene {sc['id']} has no spoken words in vo_words.json; regenerate the voice-over")
        firsts.append(times[0][0])
        for w, (a, b) in zip(nar, times):
            words_out.append({"text": w, "start": round(a, 3), "end": round(b, 3), "scene": si, "key": norm(w) in keys})
    starts = [0.0]
    for si in range(1, len(firsts)):
        starts.append(max(starts[-1] + 0.6, firsts[si] - lead))
    end = max(audio_len, words_out[-1]["end"]) + tail
    scenes_out = [{"id": sc["id"], "start": round(starts[i], 3), "end": round(starts[i + 1] if i + 1 < len(starts) else end, 3), "audio": "vo"}
                  for i, sc in enumerate(sb["scenes"])]
    return scenes_out, words_out, end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--audio-dir")
    ap.add_argument("--chars-per-sec", type=float, default=18.0,
                    help="speaking rate used to estimate scenes without audio")
    ap.add_argument("--pad", type=float, default=0.12, help="silence after each scene's audio")
    ap.add_argument("--tail", type=float, default=0.8, help="hold on the last scene")
    args = ap.parse_args()

    proj = Path(args.project)
    sb = json.loads((proj / "storyboard.json").read_text(encoding="utf-8"))
    audio_dir = Path(args.audio_dir) if args.audio_dir else proj / "audio"

    scenes_out, words_out, t = [], [], 0.0
    clips = []
    vo = audio_dir / "vo_words.json"
    vo_audio = next((audio_dir / f"narration{e}" for e in (".mp3", ".wav", ".m4a") if (audio_dir / f"narration{e}").exists()),
                    audio_dir / "narration.mp3")
    if vo.exists() and vo_audio.exists():
        scenes_out, words_out, t = timeline_from_vo(sb, json.loads(vo.read_text(encoding="utf-8"))["words"],
                                                    ffprobe_duration(vo_audio), args.tail)
        clips = [("vo", t)]
    for si, sc in enumerate(sb["scenes"] if not clips else []):
        sid = sc["id"]
        words = sc["narration"].split()
        keys = {norm(k) for k in sc.get("keywords", [])}
        audio = find_audio(audio_dir, sid) if audio_dir.exists() else None
        if audio:
            adur = ffprobe_duration(audio)
            dur = adur + sc.get("pad", args.pad)
            clips.append((audio, dur))
        else:
            est = sum(spoken_weight(w) for w in words) / args.chars_per_sec
            est += sum(trailing_pause(w) for w in words[:-1])
            dur = est + 0.35 + sc.get("pad", args.pad)
            clips.append((None, dur))
        dur = max(dur, sc.get("min_duration", 1.2))
        if si == len(sb["scenes"]) - 1:
            dur += args.tail
        timings = time_scene_words(words, dur - sc.get("pad", args.pad) - (args.tail if si == len(sb["scenes"]) - 1 else 0),
                                   audio)
        for w, (a, b) in zip(words, timings):
            words_out.append({"text": w, "start": round(t + a, 3), "end": round(t + b, 3), "scene": si,
                              "key": norm(w) in keys})
        scenes_out.append({"id": sid, "start": round(t, 3), "end": round(t + dur, 3), "audio": str(audio) if audio else None})
        t += dur

    pages = []
    for p in paginate(words_out):
        start = words_out[p[0]]["start"] - 0.05
        pages.append({"words": p, "start": round(max(start, 0), 3)})
    for i, pg in enumerate(pages):
        last = words_out[pg["words"][-1]]
        nxt = pages[i + 1]["start"] if i + 1 < len(pages) else t
        scene_end = scenes_out[last["scene"]]["end"]
        pg["end"] = round(min(nxt, max(last["end"] + 0.35, min(nxt, scene_end))), 3)

    timeline = {"duration": round(t, 3), "scenes": scenes_out, "words": words_out, "pages": pages,
                "has_audio": all(c[0] for c in clips)}
    (proj / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1), encoding="utf-8")

    if clips and clips[0][0] == "vo":
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(vo_audio), "-af",
                        f"aresample=48000,aformat=channel_layouts=mono,apad=whole_dur={t:.3f}", str(proj / "narration.wav")], check=True)
    elif timeline["has_audio"]:
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
        for a, _ in clips:
            cmd += ["-i", str(a)]
        parts = "".join(f"[{i}:a]aresample=48000,aformat=channel_layouts=mono,apad=whole_dur={d:.3f}[a{i}];"
                        for i, (_, d) in enumerate(clips))
        parts += "".join(f"[a{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=0:a=1[out]"
        cmd += ["-filter_complex", parts, "-map", "[out]", str(proj / "narration.wav")]
        subprocess.run(cmd, check=True)

    missing = [s["id"] for s in scenes_out if not s["audio"]]
    print(json.dumps({"duration": timeline["duration"], "scenes": len(scenes_out), "words": len(words_out),
                      "pages": len(pages), "has_audio": timeline["has_audio"],
                      "scenes_without_audio": missing}, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
