# Style: bedah (flat toon 3D cutaway)

For "kok bisa?" videos about one everyday object: magic com, presto, meteran listrik/air, MCB, motor
matic, termos, kipas angin, dispenser. The picture is one 3D model on a Three.js stage that is cut open, lit
flat and outlined, so it looks like a technical illustration that moves. Scene SVGs stay empty.

## Look

- **Ground**: near-white `#f7f7f5`, optional floor slab + soft contact shadow (`stage.room()`), a white
  fade behind the header so the model slides under it.
- **Model**: flat toon shading (3-step ramp), thin dark outlines on every edge, light-grey/white bodies,
  dark rubber, copper/orange heating parts, blue magnets/water side, green PCBs, glass and water
  see-through. Fixed isometric camera; a shot is only target + zoom (rarely a small yaw).
- **Cutaway**: `wedge` (default) removes the front quarter so you look into the object; `plane` cuts
  the front half. Animate open on "Kita cek rahasianya" (`setCut` 3 → 0 over ~1.1 s).
- **Highlight**: the part the narrator names turns **yellow** (`S.glow`) for as long as it is talked
  about. Everything else stays grey. This is the single most important rule of the look.
- **Header** (fixed, top-left): beat title (Inter 800, black, `*red*` emphasis, ≤ 2 lines), under it a
  big mono **readout** of the real quantity (°C, rpm, kWh, m³, A, kg/cm²) that moves with the mechanism
  (red while "hot"), a **sparkline** of that value with dashed threshold lines (e.g. 100 for boiling), a
  **badge** for the state (`go` green: normal · `warn` red: hot/fault/empty · `slow` amber: GERAK LAMBAT
  · `note` grey) and a small **sub** line (JAM 06.00, +20 menit, 0 km/h).
- **Callouts**: black uppercase pills with an arrow, pinned to a 3D point (`S.label`), pop in on the word.
- **Bunyi**: onomatopoeia in comic yellow with a thick dark outline, tilted (KLOP!, KLIK!, SSSRUUT!,
  BRRRT!); `blue` and `red` variants with white outline for alarms and state changes ("PANAS!").
- **Captions**: dark rounded pill in the middle (y ≈ 1230), Inter 800, spoken word on a yellow
  highlight, coming words dimmed.
- **Cards** (optional): white rounded panel for things that have no shape (a token's contents, a
  calculation): `S.card(html, {...})`.
- **Music**: `bedah` soft lo-fi bed (92 bpm); the object's own foley is loud and on the word: `klik`,
  `hiss`, `rev`, `relay`, `beep3`, `boil`, plus `pop`/`whoosh` for callouts and cuts.

## Clay variant (`BEDAH_OPTS.look = 'clay'`)

Soft toy-like render for house / room scale stories: `MeshStandardMaterial` (matte, warm), soft
shadows from one key light (`shadowSize`, `shadowMap` options), no ink outlines, cream ground
(`ground: 0xf3ece0`), the header fade turns cream. Use `B.rbox(w, h, d, r, 1, bevel)` with a small bevel
for rounded clay edges. `render.py` uses the real GPU (ANGLE/D3D11); on SwiftShader (`--cpu`, no GPU)
clay is slow (≈ 3 frames/s: a 60 s video ≈ 10 min). Keep the shadow map at 1024.

Camera framing at house scale (9:16 is narrow): the whole 7×8 m house needs zoom ≈ 0.42; a single
room ≈ 0.9; a top-down floor plan zoom 0.5 with pitch 0.8 (pitch 1 = blown-out floor + long wall
shadows); a device close-up 15–30. Interpolate zoom in log space when keys jump from 0.4 to 30
(`kf` on `Math.log(zoom)`, then `Math.exp`, and copy the array `kf` returns, it can be the key itself),
or the in-between frames sit far too close (a screen full of roof tiles). Check stills between keys,
not only on them.

`lib/30-rumah.js` — `BEDAH.rumah(S)` builds a reusable dollhouse cutaway: soil block cut open at the
front (the camera can go "through the floor"), wood floor, three rooms (kamar L, dapur M, ruang R),
back roof slope + gables, power pole, hanging bulbs. Returns `{ group, roof, rooms, light(name|'all',
k), darkness(name|'all', k), anchors: {meter, panel, kitchen, washer, roofRod, soilRod, poleTop, …},
cut }`. Call `stage.setCut(R.cut)` every frame and `R.roof.visible = false` for top-down shots.

Camera for houses: wide shots isometric (yaw 0); interior close-ups need `yaw ≈ -0.6` (look in through
the open front), or walls hide low objects; a hero close-up straight on uses `yaw ≈ -0.68`;
`pitch 1` = top-down (floor plan). `stage.setCamera(target, zoom, yaw, pitch, S.shake(t, keys))`.

More helpers:
- `stage.cable(points, {r, color, core, particleColor, n, opacity})` → transparent cable with a copper
  core; `.grow(k)` draws the first k of it (a cable sliding in), `.flow(t, {on, speed, color, reach})`
  moves glowing particles inside (yellow = normal current; set `color` red for overload).
- `stage.setDim(k)` dims all lights (power cut), `stage.setSky(color)` (storm).
- `S.flash(obj, at, color, dur)` short emissive glint (blue = solution), `S.danger(obj, a, b)` red,
  `S.popIn(obj, at)` bounce in (or write your own presence function when the object must exist at the
  hook too, see `listrik-rumah-aman`), `S.shake(t, [[t, amp], …])` → camera shake offset.
- Storyboard `music_mute: [[sid, word|null, sid, word|null]]` silences the music bed between two points
  (a held silence after a decisive click). SFX for electricity: `zap`, `spark`, `klik`, `relay`,
  `hum` (ambience), `rewind`, `ding`, `thunder`, `rumble`, `heartbeat`.

## Real-object workflow (do this before modelling)

1. **Research**: `python scripts/refs.py projects/<slug> "item=q1;q2" …` downloads reference photos and
   makes `refs/sheet_<item>.png`. Look at each sheet (and one full-size photo of the hero object). Also read
   how it is installed in Indonesia (PLN, PUIL, the manufacturer's manual): order of parts, mounting height,
   cable routes.
2. **Spec**: write `projects/<slug>/refs/SPEK.md` — per object: real size (m), colours, visible parts
   (display, keys, labels, terminals, seals), mounting point and height; the real installation route.
3. **Model to scale** (1 unit = 1 m) from the spec. Proportions first, then the details that make it
   recognisable (keypad + green enter on a prepaid meter, TEST button on an RCCB, louvre on an AC…); draw
   printed faces as canvas textures, brand-free.
4. **Gallery check**: render each object alone (`projects/_galeri-listrik` pattern) and compare with its
   photo before using it in the film. Fix shape and proportion problems here, not in the film.
5. **House/scene check**: render stills from every planned camera angle; make sure walls, ceiling or
   roof do not block the subject (interior shots: `pitch -1`, `yaw -0.68`).

Library: `lib/40-listrik.js` — `BEDAH.listrik(S)` → `kwhMeter()` (prepaid, `.userData.setDisplay`,
`.leds`), `mcb({label, sub, toggle})`, `rccb()`, `boxMcb({modules})` (`.userData.modules[i].userData.lever`),
`pole()`, `earthRod({len})`, `splitzen()`, `acSplit()`, `fridge()`, `riceCooker()`, `washer()`, `socket()`,
`lightSwitch()`, `ceilingLamp()` (`.userData.bulbMat`), `hand()`, `tex(w, h, draw)`.
`lib/30-rumah.js` — `BEDAH.rumah(S)`: 7×8 m perumahan house in metres (clay-tile gable roof facing the
street, trusses, plafon, keramik floor, windows with kusen, partitions with doorways, soil block), dollhouse
cut at z = 3 (`setCut(R.cut)`), roof + ceiling lid `R.lift(k)`, `R.light/darkness(room, k)`, anchors for
the meter, box MCB, AC, fridge, counter, washer, sockets, earth rods and the roof rod.

## Project files

```
projects/<slug>/
├── storyboard.json   genre "bedah", style "bedah", chrome {badge, badge_kind, sub} global + per scene
├── model.js          the 3D object and its motion (below)
├── gen_scenes.py     writes empty scenes/sNN.svg + texts (beat title per scene, bunyi on its word)
```

Template: `projects/termos-bedah/` (vacuum flask; lathe bodies, wedge cut, particles, labels, glows).
Template (clay, a house built up step by step, loop ending): `projects/listrik-rumah-aman/`.
Template (clay, a machine built up from a bucket and pulley, two "sets" swapped mid-film, a camera that rides
with a moving part, a 2D sepia history scene, a reveal into a lobby): `projects/lift-bongkar/`.

`lib/45-lift.js` — `BEDAH.lift(S)`: `rope(r, 'hemp'|'wire')` (`.userData.set(a, b)` each frame),
`ropeArc(R, r, a0, a1)`, `bucket()`, `woodPulley()`, `machine({r})` (traction machine, `.userData.wheel`),
`sheave({r})`, `rail(len, dir, {wall|back})` (T profile + brackets), `car({railX})` (cabin + sling + guide shoes
+ safety gear: `.userData.setGrip(k)`, `.lever`, `.link`, `.front`, `.setDoors(k)`, `.hitchY`, `.govAttach`),
`counterweight()`, `governor()` (`.setFly(k)`, `.setLatch(k)`), `tensionPulley()`, `person()` (`.arms`), `fist()`.
`lib/35-gedung.js` — `BEDAH.gedung(S, {shaft, pit, floorH, floors, wing, holes})`: building cross-section
around a lift shaft (pit + buffers, concrete walls, slabs with furniture, machine room, lobby with landing
doors, call button, floor indicator); `stage.setCut(G.cut)` for the shaft, `G.lobby.visible = true` +
`setCut(99)` for the lobby; `G.setDoors(k)`, `G.setCall(k)`, `G.setIndicator('G', ±1)`, `G.levels`, `G.mrY`.

2D scenes inside a 3D film (a history flashback, a diagram): create a `<canvas>` in model.js, insert it in
`#overlay` before `#bd-labels` (above the 3D, under titles and captions), draw it every frame from `t`, fade
it with `style.opacity`. Sepia engraving look: a paper texture drawn once (stains, fibres, vignette), ink
lines with a seeded 8 fps jitter ("boil"), diagonal hatching for shade. See `lift-bongkar/model.js`.
SFX for machines and lifts: `creak` (wooden pulley), `rope`, `drip`, `breath`, `motor`, `strain` (overloaded
motor with coughs), `glide`, `fray`, `snap`, `fall`, `spin` (governor), `klang`, `screech` (steel on rail),
`chop` (axe), `gasp`, `cheer`, `ting` (lift chime), `door`.

## model.js contract

```js
BEDAH.film(S => {
  const { stage, THREE } = S, B = S.B, { C, add, scene } = stage;
  stage.room();
  const body = add(B.lathe([[0,0],[0.8,0],[0.8,2.6],[0.4,3]]), C.shell);   // clipped shell
  S.label('MAGNET', magnet, [0, 0.1, 0], { from: S.at('s04', 'magnet'), to: S.end('s05') });
  S.glow(magnet, S.at('s04', 'magnet'), S.end('s05'));
  const cam = [[0, [0, 1.5, 0, 1.2]], [S.at('s03', 'rahasianya'), [0, 1.5, 0, 1.1]], [S.start('s04'), [0.3, 0.4, 0.3, 2.4]]];
  return {
    frame(t, si) { const c = B.kf(t, cam); stage.setCamera(c.slice(0, 3), c[3]); stage.setCut(B.kf(t, cutKeys)); ... },
    readout(t) { return { value: 100.6, unit: '°C', decimals: 1, hot: true }; },   // optional header number
    spark: { min: 20, max: 110, lines: [100], window: 6 },                     // optional sparkline
  };
});
```

- `S.at(sid, word, off)` / `S.end(sid[, word])` / `S.start(sid)` / `S.duration`: absolute seconds from
  the voice timeline (missing words are reported as a page error). `S.ramp(t, a, d)`, `S.on(t, a, b)`.
- `stage`: `add(geo, mat, parent, pos, rot, edges=true)`, `C.<name>` materials, `room(o)`,
  `setCamera([x,y,z], zoom, yaw)`, `setCut(c)`, `toScreen(obj, p)`. Options before the film:
  `window.BEDAH_OPTS = { look: 'toon'|'clay', cut: 'wedge'|'plane', ground, camDir: [...], palette: {name: [hex, clipped]} }`.
- Materials: clipped (cut by the cutaway, both faces) `shell grey steelClip darkClip copper brass
  blueClip redClip glass water`; solid (internals) `shellSolid greySolid steel dark ink copperSolid
  brassSolid yellow blue red green orange cream wood`. New colours go in `BEDAH_OPTS.palette`.
- Geometry: `B.cyl(r,h)`, `B.tube(r,h)` (open: you can see in), `B.box`, `B.rbox(w,h,d,r)`,
  `B.lathe([[r,y],...])`, `B.gearGeo`, `B.coil(r,h,turns)`, `B.polyShape`, `B.ALONG_X/Z`.
- Time: `B.kf(t, keys)` (smoothstep between keys; values may be arrays), `B.integrate(t, rateKeys)`
  (angle from rpm, litres from flow), `B.wheelPos` (odometer digits), `B.hash(n)` (seeded noise).

## Rules that keep it right

1. Everything is a pure function of t (no clock, no `Math.random`, no rAF). Particles: phase from
   `B.hash(i)`, position from `(t * speed + phase) % 1`.
2. Shells use clipped materials, moving parts solid ones; a part you must see into is an open `tube`.
3. Parts that touch are offset ~0.02 (no coplanar faces → no flicker).
4. One shot per beat; zoom 1.0-1.3 wide, 2-3 close-up. Cut open once, on "rahasianya". Never spin the
   camera around: the angle is the brand.
5. Put particles you want seen "inside" a cut wall on the cut faces (x ≈ 0 or z ≈ 0).
6. Readout numbers that are not in a source are an illustration: never say them in the narration.
7. Brand-free objects: no real logos or brand names on the model.

## Shot ideas

- Hook: close on the sound-making part (latch, valve, buzzer) + bunyi word, readout already moving.
- "Kok bisa? Kita cek rahasianya.": wide, whole object, the wedge opens.
- Mechanism: one part per beat, yellow, with a callout; arrows/particles show flow, heat, current.
- Slow-motion beat (badge `GERAK LAMBAT`): the key moment (air sucked out of the gap, a valve opening, a latch letting go).
- Fault beat (badge `warn`, red readout): the safety part (valve, bimetal) acts.
- Closer: back to the wide shot, everything grey again, the punchline title.
- CTA (always the last scene): wide shot, the cut closes again (or the object turns slowly), title
  `Mau dicek rahasia *apa lagi?*`, badge `KOMENTAR` (`note`), narration "Mau dicek rahasia apa lagi?
  Tulis di kolom komentar."
