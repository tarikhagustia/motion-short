# Style: lukis (painterly oil painting)

For dramatic natural events and disasters: eruptions, storms, tsunamis, battles at sea, "the day the
sky went dark". Reference feel: "Tambora". The whole picture is one painting on a canvas, redrawn every
frame by `paint.js`; the scene SVGs stay empty (only `texts` are used).

## Look

- **Painting** (`paint.js`, `window.Paint`): the backdrop is painted once with flow-field multi-bristle
  strokes (under-paint blur + 3 stroke passes); moving parts are painted each frame: billowing smoke
  puffs of smeared dabs (offscreen layer + blur), additive glow, ballistic embers, procedural lightning,
  vignette, film grain. Everything is seeded and a pure function of t.
- **Colour**: night indigo sky, sea in dark teal, fire orange/gold `#f2b85a` light.
- **Titles**: Cormorant Garamond 600, `blur` animation (letters rise out of blur); colours `cream`, `gold`;
  class `caps`; `sub` line in spaced caps. Tags: spaced uppercase serif, no box.
- **Captions**: `serif` — plain cream Cormorant 700 with a soft shadow, keywords gold.
- **Music**: `lukis` dark minor pad over a drone.

## Scenes (`storyboard.paint` + per-scene `paint`)

Short video, one place: top-level `"paint": {"scene": "volcano", "seed": 7, ...}` = one painter for the
whole video.

Several places (any longer or story-driven video): give a scene its own `"paint": {"scene": ...}`. It
starts a **segment**; following scenes without `paint` continue it (the animation stays continuous).
Segments crossfade 0.6 s, or switch hard when the scene has `transition: "cut"`. The top-level `paint`
holds the defaults (`seed`, `scary`, `blast_words`, `flash_words`, `lightning`); flashes and blasts go to
the segment they fall in. In a scene's `paint`, any `<key>_word: [sid, word, offset]` becomes `<key>` in
seconds from the segment start (e.g. `waves_word`, `rings_word`, `veil_word`, `sky_to_word`,
`wagon_word`). Ash only falls in `volcano` segments (override with `"ash": true|false`). The last 1.4 s
sink into the dark.

Painters:

| scene | what | options |
|---|---|---|
| `volcano` | eruption over the sea, smoke column, lava, embers, lightning | below, plus `waves` (tsunami wall rolling at the viewer) |
| `twilight` | red dusk sky with living swirl strokes, birds | `fg: "town"` (steeples, lit windows, crowd pointing up, `wagon` fire wagon crossing), `"fjord"` (hills, water, bridge rail, lone walker) or `"beach"` (palms, a far volcano plume, `wave`: a tsunami wall rises on the horizon, the sea drains, a crowd flees across the sand; pair with real scream recordings as `file` cues, or the synthetic `screams` SFX); `sky: "ash"` (blood-red bands) or `"nacreous"` (iridescent mother-of-pearl clouds); `sky_to` crossfades ash → nacreous |
| `globe` | painted Earth in painted space, sunlit, Krakatau ember marker | `lon: [from, to]` facing longitude over the segment, `lat` tilt, `mark: [lat, lon]`, `rings` (pressure-wave circles out and back), `veil` (ash haze spreading from the mark), `radius` |

`volcano` options: `seed`, `cx` (540), `horizon` (1180), `peak` (880), `coneW` (300), `zoom` [a, b],
`ramp` [start, end] eruption strength, `puffs` (170) / `perPuff` (26) smoke density,
`flash_words` [[sid, word, offset]] lightning on words, `lightning` [seconds] extra lightning.

### Scary mode (`"scary": true`) — for terrifying events

Adds: constant tremor, darkened sky (the lit column stands out of black), ash fall with blurred
foreground flecks, a red vignette pulsing on a 0.92 s heartbeat, a cold grade, and the text shakes.
Title `gold` turns fire red-orange, keywords red `#ff6a3a`.
`blast_words` [[sid, word, offset]] = big explosions: white flash, hard camera shake, soft broken
shockwave rings in the air and on the sea, 28 lava bombs.
`sound.py` adds the dread layer automatically: rising sub drone + wind, heartbeat, boom + impact + fire
on each blast, thunder on each `lightning` time.

Recipe that worked (Anak Krakatau, 13 s): blasts on the 2-3 key words, ~1 extra lightning every 1.3 s,
`ramp: [0.85, 1.45]`, `puffs: 190`, the name title in `gold`.

```json
"paint": {"scene": "volcano", "seed": 7, "zoom": [1.0, 1.1], "scary": true,
          "flash_words": [["s01", "muncul", 0.05], ["s02", "Krakatau", 0.1]],
          "blast_words": [["s01", "muncul", 0.05], ["s02", "Krakatau", 0.1], ["s02", "1883"]],
          "lightning": [1.25, 2.7, 5.7, 6.5, 8.9, 11.5, 12.5], "ramp": [0.85, 1.45], "puffs": 190}
```

## Engines

Both engines draw the same frame from the same `paint.js`:
- `render.py` (default): ~6 s render per second of video.
- `hyperframes.py`: ~2.4x faster, Studio preview, needs internet + Node. See SKILL.md step 8.

## Adding a scene

Write a new painter in `paint.js` (contract: `fn(canvas, opt)` returns `{render(t), flashes, shakeAt(t)}`,
`t` local to its segment, honour `opt.duration`, `opt.zoom`, and skip the finishing pass when
`opt.post === false`), add it to `API`, and use it as a scene `paint.scene`. Reuse `paintField` (backdrop
painted once from `colorAt` + `angleAt`), `stroke`, `smear`, `fbm`, `rng`, `birdsDraw`, `post`.
Ideas: `storm_sea`, `forest_fire`, `ash_city`, `ship_deck`, `village`.

Recipe that worked (Krakatau langit merah, misteri, 62 s): twilight town → globe → volcano (2 blasts)
→ globe rings → twilight beach + wave (crowd fleeing, screams) → globe veil → twilight fjord with `sky_to` on "awan".

## Known gaps

Smoke dabs can still look capsule-like up close (a sprite brush texture would help). Globe land is
coarse (simple continent polygons). Silhouettes (people, wagon, walker) are simple shapes.
