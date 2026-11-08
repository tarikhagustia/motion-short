#!/usr/bin/env python3
"""Render a motion-shorts project to a 1080x1920 MP4 (or to preview stills).

Usage:
    python render.py PROJECT_DIR                       # full video -> PROJECT_DIR/video.mp4
    python render.py PROJECT_DIR --stills              # one PNG per scene + contact sheet, fast
    python render.py PROJECT_DIR --at 3.2 7.5          # PNG at given seconds
    python render.py PROJECT_DIR --fps 30 --out x.mp4  # options

Reads storyboard.json, timeline.json (run build_timeline.py first) and scenes/<id>.svg.
Muxes narration.wav (if present) and optional --music track (ducked under the voice).
Needs: python playwright (with Chromium) and ffmpeg.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sound import paint_config  # noqa: E402  (shared lukis resolver)

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "template.html"
SYMBOLS = SKILL_DIR / "assets" / "symbols.svg"
FONT_DIR = SKILL_DIR / "assets" / "fonts"
STYLE_DIR = SKILL_DIR / "styles"

# family name -> (file, weight range)
FONTS = {
    "Lora": ("Lora-Variable.ttf", "400 700"), "Poppins": ("Poppins-Bold.ttf", "700"),
    "Playfair Display": ("PlayfairDisplay.ttf", "400 900"), "Mulish": ("Mulish.ttf", "200 1000"),
    "Fredoka": ("Fredoka.ttf", "300 700"), "Nunito": ("Nunito.ttf", "200 1000"),
    "Chakra Petch": ("ChakraPetch-Bold.ttf", "700"), "Lexend": ("Lexend.ttf", "100 900"),
    "Share Tech Mono": ("ShareTechMono.ttf", "400"),
    "Cormorant Garamond": ("CormorantGaramond.ttf", "300 700"),
}


def font_faces():
    out = [f'@font-face {{ font-family: "{fam}"; src: url("{(FONT_DIR / f).as_uri()}") format("truetype"); font-weight: {w}; }}'
           for fam, (f, w) in FONTS.items() if (FONT_DIR / f).exists()]
    semi = FONT_DIR / "ChakraPetch-SemiBold.ttf"
    if semi.exists():
        out.append(f'@font-face {{ font-family: "Chakra Petch"; src: url("{semi.as_uri()}") format("truetype"); font-weight: 600; }}')
    med = FONT_DIR / "Poppins-Medium.ttf"
    if med.exists():
        out.append(f'@font-face {{ font-family: "Poppins"; src: url("{med.as_uri()}") format("truetype"); font-weight: 500; }}')
    return "\n".join(out)


def load_style(name):
    d = STYLE_DIR / name
    if not d.is_dir():
        raise SystemExit(f"unknown style '{name}'. Available: {', '.join(p.name for p in STYLE_DIR.iterdir() if p.is_dir())}")
    rd = lambda f: (d / f).read_text(encoding="utf-8") if (d / f).exists() else ""
    cfg = json.loads(rd("style.json") or "{}")
    return cfg, rd("style.css"), rd("overlay.html"), rd("chrome.html"), rd("paint.js") + chr(10) + rd("style.js")


def load_svg(path, idx):
    svg = path.read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
    svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg)
    # make ids unique per scene so gradients/filters from different scenes don't collide
    ids = set(re.findall(r'\bid="([^"]+)"', svg))
    for i in sorted(ids, key=len, reverse=True):
        new = f"s{idx}-{i}"
        svg = re.sub(rf'\bid="{re.escape(i)}"', f'id="{new}"', svg)
        svg = re.sub(rf'url\(#{re.escape(i)}\)', f'url(#{new})', svg)
        svg = re.sub(rf'href="#{re.escape(i)}"', f'href="#{new}"', svg)
    # force the stage size and the art class
    m = re.search(r"<svg\b[^>]*>", svg)
    if not m:
        raise SystemExit(f"{path} has no <svg> root")
    tag = m.group(0)
    new_tag = re.sub(r'\s(width|height|class)="[^"]*"', "", tag)
    if "viewBox" not in new_tag:
        new_tag = new_tag[:-1] + ' viewBox="0 0 1080 1920">'
    if "xmlns=" not in new_tag:
        new_tag = new_tag[:-1] + ' xmlns="http://www.w3.org/2000/svg">'
    new_tag = new_tag[:-1] + ' class="art" width="1080" height="1920" preserveAspectRatio="xMidYMid slice">'
    return svg.replace(tag, new_tag, 1)


def build_html(proj, sb, tl):
    scenes_html = []
    for i, sc in enumerate(sb["scenes"]):
        svg_path = proj / sc.get("svg", f"scenes/{sc['id']}.svg")
        art = load_svg(svg_path, i)
        scenes_html.append(
            f'<div class="scene" id="scene-{i}"><div class="cam">{art}'
            f'<svg class="fx" viewBox="0 0 1080 1920"></svg></div></div>')
    symbols = SYMBOLS.read_text(encoding="utf-8") if SYMBOLS.exists() else ""
    cfg, css, overlay, chrome, sjs = load_style(sb.get("style", "buku"))
    pick = lambda k, d: sb.get(k, cfg.get(k, d))
    data = {
        "scenes": [{k: sc.get(k) for k in ("id", "texts", "effects", "camera", "transition", "chrome")} for sc in sb["scenes"]],
        "caption_style": pick("caption_style", "ribbon"),
        "caption_y": pick("caption_y", 1380),
        "fade": pick("fade", 0.4),
        "title_color": pick("title_color", "dark"),
        "title_anim": pick("title_anim", "blur"),
        "letter_delay": pick("letter_delay", 0.045),
        "chrome": {**cfg.get("chrome", {}), **sb.get("chrome", {})},
        "paint": paint_config(sb, tl) if sb.get("style") == "lukis" else sb.get("paint", {}),
        "timeline": tl,
    }
    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("{{FONT_FACES}}", font_faces())
    html = html.replace("{{STYLE_CSS}}", css).replace("{{OVERLAY}}", overlay).replace("{{CHROME}}", chrome)
    html = html.replace("{{STYLE_JS}}", sjs)
    html = html.replace("{{SCENES}}", symbols + "\n" + "\n".join(scenes_html))
    html = html.replace("{{DATA}}", json.dumps(data, ensure_ascii=False))
    out = proj / ".render.html"
    out.write_text(html, encoding="utf-8")
    return out


def open_page(html_path):
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(args=["--allow-file-access-from-files", "--disable-web-security"])
    page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(html_path.as_uri())
    page.evaluate("window.READY")
    if errors:
        print("Page errors:\n  " + "\n  ".join(errors), file=sys.stderr)
    return pw, browser, page


def shot(page, t, path=None, fmt="jpeg"):
    page.evaluate(f"renderAt({t:.4f})")
    kw = {"type": fmt, "clip": {"x": 0, "y": 0, "width": 1080, "height": 1920}}
    if fmt == "jpeg":
        kw["quality"] = 92
    if path:
        kw["path"] = str(path)
    return page.screenshot(**kw)


def contact_sheet(paths, out):
    from PIL import Image, ImageDraw
    thumbs = [Image.open(p).resize((270, 480)) for p in paths]
    cols = min(5, len(thumbs))
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 280 + 10, rows * 520 + 10), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    for i, (im, p) in enumerate(zip(thumbs, paths)):
        x, y = 10 + (i % cols) * 280, 10 + (i // cols) * 520
        sheet.paste(im, (x, y))
        d.text((x + 4, y + 486), Path(p).stem, fill=(230, 230, 230))
    sheet.save(out)


def mux(proj, silent, out, tl, args):
    """Mix narration + sfx (ducked under the voice) + optional music onto the silent video."""
    narration, sfx = proj / "narration.wav", proj / "audio" / "sfx.wav"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(silent)]
    labels, filt, idx = [], [], 1
    if narration.exists():
        cmd += ["-i", str(narration)]
        filt.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[v][vk]")
        labels.append("[v]")
        idx += 1
    if sfx.exists():
        cmd += ["-i", str(sfx)]
        filt.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,volume={args.sfx_volume}[s0]")
        if narration.exists():  # duck effects a little while the voice speaks
            filt.append("[s0][vk]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=300[s]")
        else:
            filt.append("[s0]anull[s]")
        labels.append("[s]")
        idx += 1
    elif narration.exists():
        filt.append("[vk]anullsink")
    music = args.music or (str(proj / "audio" / "music.wav") if (proj / "audio" / "music.wav").exists() and not args.no_music else None)
    if music:
        cmd += ["-stream_loop", "-1", "-i", music]
        filt.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,volume={args.music_volume},"
                    f"afade=t=out:st={max(tl['duration'] - 1.5, 0):.2f}:d=1.5[m0]")
        if narration.exists():
            filt[0] = filt[0].replace("asplit=2[v][vk]", "asplit=3[v][vk][vk2]")
            filt.append("[m0][vk2]sidechaincompress=threshold=0.04:ratio=5:attack=30:release=500[m]")
        else:
            filt.append("[m0]anull[m]")
        labels.append("[m]")
        idx += 1
    if labels:
        filt.append("".join(labels) + f"amix=inputs={len(labels)}:duration=longest:normalize=0,"
                    f"atrim=0:{tl['duration']:.3f},loudnorm=I=-14:TP=-1.5[a]")
        cmd += ["-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--out")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--stills", action="store_true", help="render one still per scene + contact sheet")
    ap.add_argument("--at", type=float, nargs="*", help="render stills at these times (seconds)")
    ap.add_argument("--music", help="optional background music file (looped, ducked to --music-volume)")
    ap.add_argument("--music-volume", type=float, default=0.22)
    ap.add_argument("--no-music", action="store_true", help="ignore audio/music.wav")
    ap.add_argument("--sfx-volume", type=float, default=0.9)
    ap.add_argument("--remux", action="store_true", help="only redo the audio mix on the last rendered frames (fast)")
    args = ap.parse_args()

    proj = Path(args.project).resolve()
    sb = json.loads((proj / "storyboard.json").read_text(encoding="utf-8"))
    tl_path = proj / "timeline.json"
    if not tl_path.exists():
        raise SystemExit("timeline.json not found: run build_timeline.py first")
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    if args.remux:
        silent = proj / ".video_silent.mp4"
        if not silent.exists():
            raise SystemExit("no previous render to remux; run a full render first")
        out = Path(args.out) if args.out else proj / "video.mp4"
        mux(proj, silent, out, tl, args)
        print(json.dumps({"video": str(out), "remuxed": True}))
        return
    html = build_html(proj, sb, tl)
    pw, browser, page = open_page(html)
    try:
        if args.stills or args.at is not None:
            outdir = proj / "stills"
            outdir.mkdir(exist_ok=True)
            times = args.at if args.at else []
            names = []
            if args.stills:
                for s in tl["scenes"]:
                    # a moment in the scene where the first caption is partly spoken
                    # late in the scene, so timed beats (pop/draw/grow, titles) are visible
                    times.append(s["start"] + (s["end"] - s["start"]) * 0.8)
            for t in times:
                p = outdir / f"t{t:06.2f}.png"
                shot(page, t, p, fmt="png")
                names.append(p)
            if args.stills:
                contact_sheet(names, outdir / "contact_sheet.png")
            print(json.dumps({"stills": [str(n) for n in names],
                              "contact_sheet": str(outdir / "contact_sheet.png") if args.stills else None}))
            return

        out = Path(args.out) if args.out else proj / "video.mp4"
        silent = proj / ".video_silent.mp4"
        n = int(tl["duration"] * args.fps + 0.5)
        ff = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                               "-f", "image2pipe", "-framerate", str(args.fps), "-c:v", "mjpeg", "-i", "-",
                               "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p",
                               "-r", str(args.fps), str(silent)], stdin=subprocess.PIPE)
        t0 = time.time()
        for f in range(n):
            ff.stdin.write(shot(page, f / args.fps))
            if f % (args.fps * 5) == 0:
                print(f"frame {f}/{n}  {time.time() - t0:.0f}s", file=sys.stderr)
        ff.stdin.close()
        ff.wait()
    finally:
        browser.close()
        pw.stop()

    mux(proj, silent, out, tl, args)
    (proj / ".render.html").unlink(missing_ok=True)
    print(json.dumps({"video": str(out), "duration": tl["duration"], "frames": n, "fps": args.fps,
                      "has_narration": (proj / "narration.wav").exists(), "has_sfx": (proj / "audio" / "sfx.wav").exists(),
                      "render_seconds": round(time.time() - t0)}))


if __name__ == "__main__":
    main()
