# Style: hud (sci-fi simulation screen)

For "bagaimana kalau…" scenarios, space, physics, Earth science, anything with numbers that change.
Reference feel: "Lompat ke lubang tembus Bumi".

## Look

- **Ground**: `space_bg` near-black with faint cyan grid, central bloom, twinkling stars.
  Overlay adds scanlines, a slow scan band, noise and a dark vignette.
- **Colour**: neon cyan `C #5fe3ff` for UI and neutral data; orange `O #ffae4a` for heat, danger and the
  key number; ice `#e8f6ff` for cold.
- **Chrome** (fixed): corner brackets, top-left `● SIM 02 · TITLE` + `STATUS: <value>`, top-right
  `WAKTU SIMULASI` + `T+ mm:ss` clock, mono footer (sources). Set with storyboard `chrome` and
  per-scene `chrome.status` — change the status on every beat; it's part of the storytelling.
- **Titles**: Chakra Petch, `type` animation; `light`, `cyan`, `orange` colours; stats huge with a mono `sub`.
- **Captions**: dark rounded box with glowing cyan border, Lexend SemiBold, keywords orange with glow.
- **Music**: dark synth pulse with arps (`music: "hud"`).

## Kit (`kit.py`)

`space_bg`, `glow` · bodies `dot_globe(markers=[(lat, lon, "LABEL")])`, `holo_planet`, `hot_sphere`,
`orbit_ring`, `spin_ring`, `light_pulse(path)` · UI `panel`, `readout(count_to=…)`, `meter`,
`leader_label`, `checklist`, `wave_graph`, `radar`, `hazard_strip`, `thermo`, `mono`, `big`.

## Shot ideas

- Title card: big two-line title (second line orange), hero body with spinning rings, glitch on the key verb.
- Number card: huge orange stat + a small diagram underneath (source → target with a travelling pulse).
- Dot globe with a marker on the place that matters (Jakarta), rotating.
- Event: flash + hazard strip + status change on the shock word (`transition: "cut"`).
- Diagram: orbit circle, the object leaving along the tangent (`path` anim on a dashed line).
- Data panel: readouts that count, a meter filling, a thermometer falling.
- Cross-section: layered bands with leader labels.
- Closer: status `AMAN`, the hero body returns (`grow-xy`), the reassuring number.
