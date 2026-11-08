#!/usr/bin/env python3
"""Text-to-speech through the local OmniVoice API (OpenAI-style /v1/audio/speech).

Standard library only, so it runs the same on macOS, Linux and Windows.
Long text is split at sentence boundaries, each chunk is synthesized
separately, and the pieces are joined into one audio file.

Examples:
  python tts.py --text "Halo semuanya" --out halo.wav
  python tts.py --text-file naskah.txt --out naskah.wav
  echo "Selamat pagi" | python tts.py --out pagi.wav
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import wave

DEFAULTS = {
    "url": "http://192.168.88.45:7000/v1/audio/speech",
    "model": "mlx-community/OmniVoice-bf16",
    # ref_audio is a path on the API *server* (the Mac running OmniVoice),
    # not on the machine running this script.
    "ref_audio": "/Users/devhunts/devhunts-content/arunika.mp3",
    "ref_text": "Pernahkah kamu bertanya-tanya, bagaimana sebuah kipas angin bisa menghasilkan udara yang sejuk? Sebenarnya, cara kerja kipas angin cukup menarik. Ketika kita menekan tombol ON, listrik mulai mengalir menuju motor listrik yang berada di dalam kipas.",
    "lang_code": "indonesian",
}
ENV = {
    "url": "OMNIVOICE_URL",
    "model": "OMNIVOICE_MODEL",
    "ref_audio": "OMNIVOICE_REF_AUDIO",
    "ref_text": "OMNIVOICE_REF_TEXT",
    "lang_code": "OMNIVOICE_LANG",
}


def cfg(key):
    return os.environ.get(ENV[key]) or DEFAULTS[key]


# ---------------------------------------------------------------- chunking
SENT_RE = re.compile(r"(?<=[.!?…])\s+|(?<=[.!?…][\"'”’)\]])\s+")


def _split_long(piece, max_chars):
    """Split a single over-long sentence at commas/semicolons, then spaces."""
    if len(piece) <= max_chars:
        return [piece]
    parts, out, cur = re.split(r"(?<=[,;:])\s+", piece), [], ""
    for p in parts:
        if len(p) > max_chars:  # still too long: hard-wrap on whitespace
            if cur:
                out.append(cur)
                cur = ""
            words, line = p.split(), ""
            for w in words:
                if line and len(line) + 1 + len(w) > max_chars:
                    out.append(line)
                    line = w
                else:
                    line = f"{line} {w}".strip()
            if line:
                out.append(line)
            continue
        if cur and len(cur) + 1 + len(p) > max_chars:
            out.append(cur)
            cur = p
        else:
            cur = f"{cur} {p}".strip()
    if cur:
        out.append(cur)
    return out


def chunk_text(text, max_chars):
    text = text.replace("\r\n", "\n").strip()
    chunks = []
    for para in re.split(r"\n\s*\n", text):
        para = " ".join(para.split())
        if not para:
            continue
        sentences = []
        for s in SENT_RE.split(para):
            sentences.extend(_split_long(s.strip(), max_chars))
        cur = ""
        for s in sentences:
            if not s:
                continue
            if cur and len(cur) + 1 + len(s) > max_chars:
                chunks.append(cur)
                cur = s
            else:
                cur = f"{cur} {s}".strip()
        if cur:
            chunks.append(cur)  # paragraphs never share a chunk
    return chunks


# ---------------------------------------------------------------- API call
def synthesize(text, args):
    payload = {
        "model": args.model,
        "input": text,
        "ref_audio": args.ref_audio,
        "ref_text": args.ref_text,
        "lang_code": args.lang,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last_err = None
    for attempt in range(args.retries + 1):
        req = urllib.request.Request(
            args.url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=args.timeout) as resp:
                body = resp.read()
                ctype = resp.headers.get("Content-Type", "")
            if ctype.startswith("application/json") or not body:
                raise RuntimeError(f"API returned no audio: {body[:500]!r}")
            return body, ctype
        except urllib.error.HTTPError as e:
            detail = e.read()[:800].decode("utf-8", "replace")
            last_err = RuntimeError(f"HTTP {e.code} from API: {detail}")
            if e.code < 500:  # bad request won't fix itself on retry
                break
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            last_err = ConnectionError(
                f"Could not reach the TTS API at {args.url} ({e}). It is on a local "
                "network address, so this machine must be on the same network and the "
                "OmniVoice server must be running."
            )
        if attempt < args.retries:
            time.sleep(2 * (attempt + 1))
    raise last_err


# ---------------------------------------------------------------- audio
def sniff_format(body, ctype=""):
    if body[:4] == b"RIFF" and body[8:12] == b"WAVE":
        return "wav"
    if body[:3] == b"ID3" or (len(body) > 1 and body[0] == 0xFF and body[1] & 0xE0 == 0xE0):
        return "mp3"
    if body[:4] == b"fLaC":
        return "flac"
    if body[:4] == b"OggS":
        return "ogg"
    for key, ext in (("wav", "wav"), ("mpeg", "mp3"), ("mp3", "mp3"), ("flac", "flac"),
                     ("ogg", "ogg"), ("opus", "opus"), ("aac", "aac"), ("pcm", "pcm")):
        if key in ctype:
            return ext
    return "bin"


def merge_wav(bodies, out_path, gap_ms):
    params, frames = None, []
    for b in bodies:
        with wave.open(io.BytesIO(b)) as w:
            p = (w.getnchannels(), w.getsampwidth(), w.getframerate())
            if params and p != params:
                raise ValueError("chunks have different WAV formats")
            params = p
            frames.append(w.readframes(w.getnframes()))
    nch, sw, rate = params
    silence = b"\x00" * (int(rate * gap_ms / 1000) * nch * sw)
    with wave.open(out_path, "wb") as w:
        w.setnchannels(nch)
        w.setsampwidth(sw)
        w.setframerate(rate)
        w.writeframes(silence.join(frames))
    total = sum(len(f) for f in frames) + len(silence) * (len(frames) - 1)
    return total / (rate * nch * sw)


def merge_ffmpeg(paths, out_path):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for p in paths:
            f.write("file '" + os.path.abspath(p).replace("'", "'\\''") + "'\n")
        listfile = f.name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", listfile, "-c", "copy", out_path],
            check=True,
        )
    finally:
        os.unlink(listfile)


def wav_duration(path):
    try:
        with wave.open(path) as w:
            return w.getnframes() / w.getframerate()
    except Exception:
        return None


def fix_ext(path, fmt):
    root, ext = os.path.splitext(path)
    return path if ext.lower().lstrip(".") == fmt else f"{root}.{fmt}"


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--text", help="text to speak")
    src.add_argument("--text-file", help="UTF-8 text file to speak")
    ap.add_argument("--out", required=True, help="output audio path (extension is corrected to the real format)")
    ap.add_argument("--lang", default=cfg("lang_code"), help="lang_code, e.g. indonesian, english")
    ap.add_argument("--ref-audio", default=cfg("ref_audio"), help="voice sample path ON THE API SERVER")
    ap.add_argument("--ref-text", default=cfg("ref_text"), help="exact transcript of the voice sample")
    ap.add_argument("--url", default=cfg("url"))
    ap.add_argument("--model", default=cfg("model"))
    ap.add_argument("--max-chars", type=int, default=400, help="max characters per request (default 400)")
    ap.add_argument("--gap-ms", type=int, default=250, help="silence between chunks for WAV merge")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per request")
    ap.add_argument("--retries", type=int, default=1)
    ap.add_argument("--keep-chunks", action="store_true", help="also keep the per-chunk files")
    ap.add_argument("--dry-run", action="store_true", help="only print the chunks, call nothing")
    args = ap.parse_args()

    if args.text is not None:
        text = args.text
    elif args.text_file:
        with open(args.text_file, encoding="utf-8-sig") as f:
            text = f.read()
    else:
        text = sys.stdin.buffer.read().decode("utf-8")
    chunks = chunk_text(text, args.max_chars)
    if not chunks:
        sys.exit("error: no text to synthesize")

    if args.dry_run:
        print(json.dumps({"chunks": chunks}, ensure_ascii=False, indent=2))
        return

    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)

    bodies, fmt = [], None
    for i, c in enumerate(chunks, 1):
        print(f"[{i}/{len(chunks)}] {len(c)} chars…", file=sys.stderr, flush=True)
        try:
            body, ctype = synthesize(c, args)
        except Exception as e:
            sys.exit(f"error on chunk {i}/{len(chunks)}: {e}")
        f = sniff_format(body, ctype)
        fmt = fmt or f
        bodies.append(body)

    out_path = fix_ext(args.out, fmt)
    stem = os.path.splitext(out_path)[0]
    chunk_paths, note = [], None

    def write_chunks():
        for i, b in enumerate(bodies, 1):
            p = f"{stem}_part{i:02d}.{fmt}"
            with open(p, "wb") as fh:
                fh.write(b)
            chunk_paths.append(p)

    if len(bodies) == 1:
        with open(out_path, "wb") as fh:
            fh.write(bodies[0])
    elif fmt == "wav":
        try:
            merge_wav(bodies, out_path, args.gap_ms)
        except Exception as e:
            note = f"WAV merge failed ({e}); trying ffmpeg"
            write_chunks()
            merge_ffmpeg(chunk_paths, out_path)
    elif shutil.which("ffmpeg"):
        write_chunks()
        merge_ffmpeg(chunk_paths, out_path)
    elif fmt == "mp3":
        with open(out_path, "wb") as fh:  # MP3 frames concatenate playably
            fh.write(b"".join(bodies))
        note = "ffmpeg not found; MP3 chunks were byte-joined (plays fine, duration metadata may be off)"
    else:
        write_chunks()
        out_path = None
        note = f"ffmpeg not found, cannot join {fmt}; kept separate part files"

    if chunk_paths and out_path and not args.keep_chunks:
        for p in chunk_paths:
            os.remove(p)
        chunk_paths = []

    result = {
        "output": os.path.abspath(out_path) if out_path else None,
        "format": fmt,
        "chunks": len(chunks),
        "characters": sum(len(c) for c in chunks),
        "duration_seconds": round(wav_duration(out_path), 2) if out_path and fmt == "wav" and wav_duration(out_path) else None,
        "part_files": [os.path.abspath(p) for p in chunk_paths],
    }
    if note:
        result["note"] = note
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
