# Style: emas (ornamental gold & batik)

For history, kingdoms, voyages, culture, legends, archaeology.
Reference feel: "Sriwijaya, kerajaan yang sempat hilang".

## Look

- **Ground**: fabric. `batik_bg(base, motif)` (parang lines, kawung, dots) in rust brown `#7a4a2a`,
  wine `#5e2a2a`, or `night_cloth()` deep indigo with twinkling gold dots for sea/night/sky.
- **Shapes**: flat crimson `#8e2433`, indigo `#27346b`, rust, cream — always with a thin gold outline
  (`GOLD #d9b45e`) and gold detail lines (sail battens, roof ribs, glyphs).
- **Light**: gold glows (`glow`), spiky `gold_sun`, `sparkles` that twinkle. Overlay adds weave + warm vignette.
- **Titles**: Playfair Display, gold gradient with glow, `shine` animation (rise from blur + glint).
  Stats get `unit` ("M") or `sub` ("TAHUN LALU").
- **Captions**: crimson banner with gold rules, Mulish ExtraBold white, keywords gold.
- **Music**: gamelan-like pentatonic plucks + drone + soft gong (`music: "emas"`).

## Kit (`kit.py`)

backgrounds `batik_bg`, `night_cloth` · ornaments `ornate_frame`, `rosette`, `gold_sun`, `sparkles`,
`glow`, `compass` · water `ornate_waves`, `river(path)` · buildings `rumah_panggung`, `stupa_temple` ·
nature `batik_palm`, `hill_motif` · vessels `jong` (bobbing ship) · people `traveler`, `figure_rows` ·
artefacts `prasasti`, `medallion`, `lamp` · maps `land(path)`, `route(path, at, dur)`, `label_gold`.

## Shot ideas

- Framed vignette (`ornate_frame` + subject inside) as the opener.
- Map: `land()` coastlines on indigo `ornate_waves`, `route()` drawing on the anchor word, a boxed distance.
- River settlement: `river()` S-curve + `rumah_panggung` on both banks + `batik_palm` (very dense).
- Word/artefact cards: `medallion` + arrow + crimson box.
- Rows of figures (`figure_rows` / many `traveler`) for "ribuan biksu", "30 perempuan".
- Night navigation: constellation `draw`, wind curls drifting, boat bobbing.
- Closer: big `gold_sun` + hero object + floating gold words, glow fading in on the last key word.
