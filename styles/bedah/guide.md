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

## Project files

```
projects/<slug>/
├── storyboard.json   genre "bedah", style "bedah", chrome {badge, badge_kind, sub} global + per scene
├── model.js          the 3D object and its motion (below)
├── gen_scenes.py     writes empty scenes/sNN.svg + texts (beat title per scene, bunyi on its word)
```

Template: `projects/termos-bedah/` (vacuum flask; lathe bodies, wedge cut, particles, labels, glows).

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
  `window.BEDAH_OPTS = { cut: 'plane', camDir: [...], palette: {name: [hex, clipped]} }`.
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
