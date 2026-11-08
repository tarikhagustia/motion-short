# Engine reference: storyboard, scene SVGs, animation attributes

## Project folder

```
projects/<slug>/
├── storyboard.json      you write (texts are filled in by gen_scenes.py)
├── gen_scenes.py        you write: builds scenes/*.svg from kits + timing
├── scenes/s01.svg …     generated
├── audio/               voice.py: sNN clips, narration.wav, vo_words.json; sound.py: sfx.wav, music.wav
├── timeline.json        build_timeline.py
├── narration.wav        build_timeline.py (48 kHz mono, padded to the video length)
├── stills/              render.py --stills / --at
├── video.mp4            render.py
└── upload.txt           you write
```

## storyboard.json

Top level: `topic`, `genre` (`dokumenter` | `sains` | `misteri` | `explainer` | `sejarah`; see `genres.md`),
`style` (`emas` | `buku` | `hud` | `lukis`), optional overrides of the style defaults
(`caption_style`, `caption_y`, `title_color`, `title_anim`, `letter_delay`, `fade`, `music`),
`chrome` (hud header values: `sim`, `title`, `footer`, `clock_rate`, `clock_label`), `auto_whoosh`,
`paint` (lukis painter: `scene`, `seed`, `zoom`, `ramp`, `puffs`, `flash_words`, `lightning`, `scary`,
`blast_words`; full list in `styles/lukis/guide.md`). Word lists are `[[sid, word, offset]]`; the same
resolver (`sound.paint_times`) is used by style.js, sound.py and hyperframes.py so picture and sound line up.

Per scene:

| Field | Meaning |
|---|---|
| `id` | `s01`, `s02`, … |
| `narration` | caption text (digits) |
| `spoken` | what the voice reads (numbers written out, "…" pauses) |
| `keywords` | 1-2 caption words in the accent colour (punctuation ignored) |
| `texts` | `[{kind: title|stat|tag, text, y, size, at, until, color, class, x, align, unit, sub, anim}]` — normally written by gen_scenes.py; `at`/`until` are seconds from the scene start, i.e. exactly `T.at(sid, word)` (already scene-relative, never subtract the scene start) |
| `effects` | particle overlay: `ash dust rain snow bubbles embers leaves gold motes embers2 petals` |
| `camera` | `{zoom: [a, b], pan: [x, y], parallax}` |
| `transition` | `fade` (default) · `cut` · `zoom` |
| `chrome` | hud: per-scene header values, e.g. `{"status": "GELAP"}` |
| `paint` | lukis: start a new painter segment here, e.g. `{"scene": "globe", "rings_word": ["s06", "Gelombang"]}` (see `styles/lukis/guide.md`) |
| `sfx` | `[{kind, word | at, offset, dur, volume, ambience}]` — kinds listed in `scripts/sound.py` |

Title colours per style: emas `gold cream dark`; buku `brown red dark light`; hud `light cyan orange`
(+ class `boxed`); lukis `cream gold` (+ class `caps`; `gold` turns fire red in scary mode). Tag classes: emas `plain`; buku `small`; hud `warn`.
Title animations: `shine` (emas), `pop` (buku), `type` (hud), `blur` (lukis).

## Scene SVG

Root `viewBox="0 0 1080 1920"`; paint a full background first. Ids are made unique per scene
automatically. Build scenes in Python:

```python
import sys; sys.path[:0] = ["<skill>/scripts", "<skill>/styles/<style>"]
from svgkit import write_scene, group, depth, mix, shade
from kit import *
from timing import Timing
T = Timing(project_dir)
write_scene("scenes/s03.svg", [background(), subject(), group(callout, "pop", at=T.at("s03", "vato"))])
```

`group(content, "anim names", at=…, dur=…, period=…, amp=…, origin=…, dir=…)` → `<g data-anim … data-…>`.
`depth(content, 0.1-1)` → parallax layer.

### data-anim kinds

Loops: `drift` (speed, vy) · `float` · `bob` · `sway` (pivot) · `pulse` · `spin` · `rise` (period, dist)
· `fly` · `flicker` · `twinkle` · `ripple` · `blink` (eyes) · `glitch` · `blinkon` · `scan` · `walk` · `swing` · `chop`.

One-shots from `data-at`: `pop` · `fade` · `fade-out` · `slide-up` · `slide-in` (dist) · `grow` ·
`grow-x` · `grow-xy` · `draw` (stroke path) · `sink` · `lift` · `shake` · `fall` (angle, pivot) ·
`reveal` / `cover` (dir) · `burst` (vx, vy) · `count` (from, to, prefix, suffix on `<text>`) ·
`path` (data-path="#id", dur, loop, rotate).

Special: `globe` — children with `data-lat`/`data-lon` are projected on a rotating sphere
(`data-cx data-cy data-r data-rate data-tilt data-lon0`); used by `hud.dot_globe`.

Combine kinds with spaces (`"pop float"`). `data-pivot="x y"` rotates around a point in the
element's coordinates. `data-stagger` on a group delays its animated children one after another.
A `transform` attribute on an animated element is moved to a wrapper automatically.

## Style hook

`style.js` may set `STYLE.frame = (t, sceneIndex, tInScene) => …`; the engine calls it every frame after
the SVG animations (lukis uses it to repaint the canvas and shake the text).

## HyperFrames (lukis)

`scripts/hyperframes.py` writes `<project>/hf/`: `index.html` with `#root data-composition-id="main"`,
titles and caption pages as clips (`data-start`, `data-duration`, `data-track-index`), one `<audio>` clip
with the pre-mixed `assets/mix.wav`, a paused GSAP timeline registered as `window.__timelines["main"]`
(letters from blur, karaoke colour), and canvas painting driven by the `hf-seek` event. Same rules: pure
function of t, no wall clock. `hyperframes check` must pass before render.

## Debugging

- Blank or broken scene → run `render.py --stills` and read the "Page errors" it prints.
- Element not animating → it needs `data-anim`; `path` needs the target path's `id` in the same SVG.
- Something hidden under the caption → keep subjects inside y 260-1380.
- Text too small on phone → titles ≥ 100 px, labels ≥ 36 px.
- HF render shows no text → fonts not loaded before `__timelines` registration, or GSAP CDN offline.
- Timing off → re-run `voice.py --align-only` then `build_timeline.py`, then `gen_scenes.py`.
