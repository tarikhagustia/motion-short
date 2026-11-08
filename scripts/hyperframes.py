#!/usr/bin/env python3
"""Build (and optionally check + render) a HyperFrames version of a `lukis` project.

Usage:
    python hyperframes.py PROJECT_DIR                # writes PROJECT_DIR/hf/ and runs `hyperframes check`
    python hyperframes.py PROJECT_DIR --render       # ... then renders PROJECT_DIR/video-hf.mp4
    python hyperframes.py PROJECT_DIR --no-check

Needs the same inputs as render.py: storyboard.json (style "lukis", `paint`, scene `texts`),
timeline.json, narration.wav, audio/sfx.wav and audio/music.wav (run voice.py, build_timeline.py and
sound.py first). The painting is the shared styles/lukis/paint.js, so both engines give the same picture;
HyperFrames renders ~2.4x faster. Needs internet (GSAP from the jsDelivr CDN) and Node (npx).

PROJECT_DIR/hf/ = index.html (composition), package.json, hyperframes.json, assets/{paint.js, fonts, mix.wav}.
`cd PROJECT_DIR/hf && npx --yes hyperframes@0.8.191 preview` opens the Studio for live scrubbing.
"""
import argparse
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
from sound import paint_config  # noqa: E402

HF = "hyperframes@0.8.191"
GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"


def mix_audio(proj, dur, out):
    """narration + sfx (ducked) + music (low), loudness -14 LUFS -> one wav for the <audio> clip."""
    nar, sfx, mus = proj / "narration.wav", proj / "audio" / "sfx.wav", proj / "audio" / "music.wav"
    if not nar.exists():
        print("  ! no narration.wav: composition will be silent")
        return False
    ins, f, labels = ["-i", str(nar)], ["[0:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.15,asplit=2[v][vk]"], ["[v]"]
    i = 1
    if sfx.exists():
        ins += ["-i", str(sfx)]
        f.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.85[s0];[s0][vk]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=300[s]")
        labels.append("[s]"); i += 1
    else:
        f[0] = f[0].replace(",asplit=2[v][vk]", "[v]")
    if mus.exists():
        ins += ["-i", str(mus)]
        f.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.18,afade=t=out:st={max(dur - 1.5, 0):.2f}:d=1.5[m]")
        labels.append("[m]")
    f.append("".join(labels) + f"amix=inputs={len(labels)}:duration=longest:normalize=0,atrim=0:{dur:.3f},loudnorm=I=-14:TP=-1.5[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(f), "-map", "[a]", "-ar", "48000", str(out)], check=True)
    return True


def build(proj):
    sb = json.loads((proj / "storyboard.json").read_text(encoding="utf-8"))
    tl = json.loads((proj / "timeline.json").read_text(encoding="utf-8"))
    if sb.get("style") != "lukis":
        sys.exit("hyperframes.py only builds `lukis` projects (the painter is the whole picture)")
    dur = tl["duration"]
    out = proj / "hf"
    (out / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    shutil.copy(SKILL / "styles" / "lukis" / "paint.js", out / "assets" / "paint.js")
    shutil.copy(SKILL / "assets" / "fonts" / "CormorantGaramond.ttf", out / "assets" / "fonts" / "CormorantGaramond.ttf")
    has_audio = mix_audio(proj, dur, out / "assets" / "mix.wav")
    (out / "package.json").write_text(json.dumps({"name": f"{proj.name}-hf", "private": True, "type": "module", "scripts": {
        "dev": f"npx --yes {HF} preview", "check": f"npx --yes {HF} check", "render": f"npx --yes {HF} render"}}, indent=2), encoding="utf-8")
    (out / "hyperframes.json").write_text(json.dumps({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}, "media": {"autoProxy": True}}, indent=2), encoding="utf-8")

    paint = paint_config(sb, tl)
    flashes, blasts = paint["flashes"], paint["blasts"]
    scary = bool(paint.get("scary"))
    key_col = "#ff6a3a" if scary else "#f2b85a"

    titles = []
    for si, sc in enumerate(sb["scenes"]):
        s0, s1 = tl["scenes"][si]["start"], tl["scenes"][si]["end"]
        for tx in sc.get("texts", []):
            start = round(s0 + tx.get("at", 0.2), 3)
            end = round(s0 + tx["until"], 3) if tx.get("until") else s1
            cls = "tag" if tx["kind"] == "tag" else f'title {tx.get("color", "cream")} {tx.get("class", "")}'.strip()
            letters = "".join(f'<span class="l">{html.escape(ch) if ch != " " else "&nbsp;"}</span>' for ch in tx["text"])
            size = f'font-size:{tx.get("size", 120)}px;' if tx["kind"] != "tag" else ""
            titles.append(f'<div id="tt{len(titles)}" class="clip {cls}" data-start="{start}" data-duration="{round(end - start, 3)}" '
                          f'data-track-index="1" style="top:{tx.get("y", 230)}px;{size}">{letters}</div>')
    caps = []
    for pi, pg in enumerate(tl["pages"]):
        spans = "".join(f'<span class="w{" key" if tl["words"][wi]["key"] else ""}" data-t="{tl["words"][wi]["start"]}">'
                        f'{html.escape(tl["words"][wi]["text"])}</span>' for wi in pg["words"])
        caps.append(f'<div id="cp{pi}" class="clip cap" data-start="{pg["start"]}" data-duration="{round(pg["end"] - pg["start"], 3)}" '
                    f'data-track-index="2"><div class="box">{spans}</div></div>')
    gold = ('color:#ff7a3c;text-shadow:0 0 30px rgba(255,60,20,.7),0 0 8px rgba(255,120,60,.6),0 3px 10px rgba(0,0,0,.8)' if scary
            else 'color:#f2c46a;text-shadow:0 0 24px rgba(255,170,70,.45),0 3px 10px rgba(0,0,0,.7)')
    audio = f'<audio id="mix" src="assets/mix.wav" data-start="0" data-duration="{dur}" data-volume="1"></audio>' if has_audio else ""
    nl = "\n      "
    page = f'''<!doctype html>
<html lang="id" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="{GSAP}"></script>
    <script src="assets/paint.js"></script>
    <style>
      @font-face {{ font-family: "Cormorant Garamond"; src: url("assets/fonts/CormorantGaramond.ttf") format("truetype"); font-weight: 300 700; }}
      html, body {{ margin: 0; background: #000; }}
      #root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; background: #0b0a12; font-family: "Cormorant Garamond", serif; }}
      #paint {{ position: absolute; inset: 0; width: 1080px; height: 1920px; }}
      #grain {{ position: absolute; inset: 0; width: 1080px; height: 1920px; opacity: .07; mix-blend-mode: overlay; pointer-events: none; }}
      .title {{ position: absolute; left: 60px; right: 60px; text-align: center; font-weight: 600; letter-spacing: .02em; line-height: 1; z-index: 10; }}
      .title.cream {{ color: #f6ead2; text-shadow: 0 4px 22px rgba(0,0,0,.65), 0 1px 2px rgba(0,0,0,.6); }}
      .title.gold {{ {gold}; }}
      .title.caps {{ text-transform: uppercase; letter-spacing: .08em; }}
      .tag {{ position: absolute; left: 0; right: 0; text-align: center; color: #f0e2c4; font-weight: 600; font-size: 40px; letter-spacing: .3em;
              text-transform: uppercase; text-shadow: 0 3px 12px rgba(0,0,0,.8); z-index: 10; }}
      .l {{ display: inline-block; }}
      .cap {{ position: absolute; left: 0; right: 0; top: {sb.get("caption_y", 1440)}px; display: flex; justify-content: center; z-index: 20; }}
      .cap .box {{ max-width: 900px; text-align: center; font-weight: 700; font-size: 64px; line-height: 1.15; color: #fbf3e4;
                   text-shadow: 0 3px 14px rgba(0,0,0,.85), 0 1px 3px rgba(0,0,0,.9); }}
      .cap .w {{ display: inline-block; margin: 0 .14em; color: rgba(251,243,228,.5); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="1080" data-height="1920">
      <canvas id="paint" width="1080" height="1920" data-layout-allow-overflow></canvas>
      <canvas id="grain" width="540" height="960"></canvas>
      {nl.join(titles)}
      {nl.join(caps)}
      {audio}
    </div>
    <script>
      const DURATION = {dur}, SCARY = {str(scary).lower()};
      const painter = Paint[{json.dumps(paint.get("scene", "volcano"))}](document.getElementById("paint"), {json.dumps(paint)});

      // film grain: seeded noise, 12 new frames per second, pure function of t
      const gc = document.getElementById("grain").getContext("2d");
      function grainAt(t) {{
        const f = Math.floor(t * 12), img = gc.createImageData(540, 960);
        let s = (f * 2654435761) >>> 0 || 1;
        for (let i = 0; i < img.data.length; i += 4) {{ s = (s * 1664525 + 1013904223) >>> 0; const v = 90 + (s / 4294967296) * 120; img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 255; }}
        gc.putImageData(img, 0, 0);
      }}
      // scary: text shakes with the blasts plus a faint tremor
      const shakeEls = SCARY ? [...document.querySelectorAll(".title, .tag, .cap")] : [];
      function noise1(x) {{ const i = Math.floor(x), f = x - i, h = n => {{ let v = Math.sin(n * 127.1) * 43758.5453; return v - Math.floor(v); }}; return h(i) + (h(i + 1) - h(i)) * f * f * (3 - 2 * f); }}
      function renderAt(t) {{
        painter.render(t); grainAt(t);
        if (!shakeEls.length) return;
        const a = 1.5 + (painter.shakeAt ? painter.shakeAt(t) : 0) * 22;
        const x = (noise1(t * 36) - .5) * 2 * a, y = (noise1(t * 41 + 9) - .5) * 2 * a;
        shakeEls.forEach((el) => (el.style.translate = `${{x.toFixed(1)}}px ${{y.toFixed(1)}}px`));
      }}

      // GSAP: title letters rise from blur; caption pages fade in, words light up on their spoken time
      const tl = gsap.timeline({{ paused: true }});
      document.querySelectorAll(".title, .tag").forEach((el) => {{
        tl.fromTo(el.querySelectorAll(".l"), {{ opacity: 0, y: 22, filter: "blur(8px)" }},
          {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.3, stagger: {sb.get("letter_delay", 0.05)}, ease: "power2.out" }}, parseFloat(el.dataset.start));
      }});
      document.querySelectorAll(".cap").forEach((cap) => {{
        tl.fromTo(cap.querySelector(".box"), {{ opacity: 0, y: 18, scale: 0.96 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.15, ease: "power2.out" }}, parseFloat(cap.dataset.start));
        cap.querySelectorAll(".w").forEach((w) => {{
          const lit = w.classList.contains("key") ? "{key_col}" : "#fbf3e4";
          tl.fromTo(w, {{ color: "rgba(251,243,228,0.5)" }}, {{ color: lit, duration: 0.08, immediateRender: false }}, parseFloat(w.dataset.t));
        }});
      }});
      tl.set({{}}, {{}}, DURATION);

      window.addEventListener("hf-seek", (e) => renderAt(e.detail.time));
      document.fonts.load("700 64px 'Cormorant Garamond'").catch(() => {{}}).then(() => {{
        renderAt(0);
        window.__timelines = window.__timelines || {{}};
        window.__timelines["main"] = tl;
      }});
    </script>
  </body>
</html>
'''
    (out / "index.html").write_text(page, encoding="utf-8")
    print(f"hf/index.html: {dur} s, {len(titles)} titles, {len(caps)} caption pages, flashes {flashes}, blasts {blasts}, scary {scary}")
    return out


def npx(out, *args):
    exe = shutil.which("npx") or shutil.which("npx.cmd")
    if not exe:
        sys.exit("npx not found: install Node.js")
    r = subprocess.run([exe, "--yes", HF, *args], cwd=out)
    if r.returncode:
        sys.exit(f"hyperframes {args[0]} failed ({r.returncode})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--render", action="store_true", help="render PROJECT_DIR/video-hf.mp4 after the check")
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("-o", "--output", help="render output (default PROJECT_DIR/video-hf.mp4)")
    args = ap.parse_args()
    proj = Path(args.project).resolve()
    out = build(proj)
    if not args.no_check:
        npx(out, "check")
    if args.render:
        dest = Path(args.output).resolve() if args.output else proj / "video-hf.mp4"
        npx(out, "render", "-o", str(dest))
        print("rendered", dest)


if __name__ == "__main__":
    main()
