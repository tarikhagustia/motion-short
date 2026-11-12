---
name: motion-shorts
description: Make a ready-to-upload Indonesian fact Short (YouTube Shorts / Reels / TikTok, 9:16 MP4, 35-47 s) in the "Motionformat-like" house format - researched script with sources, cloned-voice narration (OmniVoice), word-by-word karaoke captions, richly animated scenes, synthesized SFX + music bed, and the upload text. First asks the user which gaya video they want - dokumenter (cinematic painted disasters/nature, optional terrifying mode), sains ("what if" physics/space simulation screen), misteri (dark, unexplained, open question), explainer (warm storybook "kenapa?"), sejarah (ornamental gold & batik), bedah ("kok bisa?" flat toon 3D cutaway of an everyday object) - and adapts script, tone, rhythm, look and sound to it. Use it whenever the user asks for a short / reel / TikTok / "video fakta", "video edukasi 40 detik", "shorts kayak Motionformat", "video dokumenter/misteri/sejarah singkat", "video bedah / kok bisa / cara kerja benda" (magic com, presto, meteran, MCB, motor matic), even if they only give a topic.
---

# Motion Shorts

Topic in, finished MP4 + `upload.txt` out. Two layers:
- **Gaya video** (`references/genres.md`): dokumenter · sains · misteri · explainer · sejarah · bedah. What the
  user chooses. Decides script shape, narration tone, rhythm, sound, and which look to use.
- **Tampilan** (look pack, `styles/<name>/`): emas · buku · hud · lukis · bedah. How it is drawn, so videos
  with the same look always match. Internal; don't make the user pick these names.

Everything renders locally and deterministically: scene SVGs + a time-driven HTML template, captured frame by frame with
Playwright, muxed with ffmpeg.

```
motion-shorts/
├── SKILL.md                 this file
├── assets/template.html     the engine (animations, captions, titles, chrome, particles)
├── assets/fonts/            all fonts (OFL)
├── scripts/
│   ├── voice.py             OmniVoice per scene -> audio/narration.wav + Whisper word timings
│   ├── build_timeline.py    scene / word / caption-page times -> timeline.json
│   ├── timing.py            T.at("s03", "vato") for scene generators
│   ├── svgkit.py            generic animated pieces (sky, trees, people, water, fire, ...)
│   ├── sound.py             procedural SFX + style music bed -> audio/sfx.wav, audio/music.wav
│   ├── render.py            stills / full render / remux
│   ├── refs.py              reference photos (Wikimedia Commons) + contact sheets for modelling real objects
│   ├── hyperframes.py       lukis only: HyperFrames composition (hf/) + check + render (~2.4x faster)
│   └── omnivoice_tts.py     OmniVoice client (used by voice.py)
├── styles/
│   ├── emas/  buku/  hud/   style.json, style.css, overlay.html, [chrome.html, style.js], kit.py, guide.md
│   ├── lukis/               style.json, style.css, overlay.html, style.js, paint.js (canvas painter), guide.md
│   └── bedah/               style.json, style.css, overlay.html, chrome.html, style.js, lib/ (three.js + 3D stage), guide.md
└── references/
    ├── genres.md            the six gaya: script/tone/rhythm/sound per gaya, gaya -> look, how to ask
    ├── format.md            script formula, scene rhythm, captions, upload text
    └── engine.md            storyboard fields, data-anim list, effects, chrome, debugging
```

Read `references/genres.md`, `references/format.md` and the chosen look's `guide.md` before writing. Read
`references/engine.md` when writing scenes.

## Ask the gaya first

Before research, ask which gaya the user wants (`AskUserQuestion`, rules in `genres.md` §Asking):
offer the 4 gaya that fit the topic best, recommended first, each described for *this* topic; the 5th
via "Other". For a deadly event also ask Normal vs Seram. Skip the question when the user already named
a gaya or a reference video, or said "langsung aja" — then pick and say which.

| Gaya | Tampilan | Untuk |
|---|---|---|
| dokumenter | `lukis` (`emas` if it can't be painted yet) | real dramatic events, disasters, nature |
| sains | `hud` | "bagaimana kalau…", space, physics, numbers |
| misteri | `emas` night grounds + dark sound (`lukis`+scary for natural events) | unexplained, legends, open questions |
| explainer | `buku` | "kenapa…?", animals, body, everyday science |
| sejarah | `emas` | kingdoms, figures, voyages, culture |
| bedah | `bedah` | "kok bisa?" one everyday object cut open: magic com, presto, meteran, MCB, motor matic |

Looks: `emas` batik cloth + gold outlines + gamelan · `buku` watercolour paper + cute pencil characters +
music box · `hud` near-black screen, neon cyan/orange, panels, meters, synth · `lukis` one living oil
painting (smoke, fire, lightning), serif titles from blur, dark pad; `paint.scary` = blasts, shake,
ash, red heartbeat, dread audio. · `bedah` near-white ground, one flat-toon 3D model (Three.js) cut open
with a wedge, the named part turning yellow, black callout pills, mono readout + sparkline + state badge
header, dark caption pill with the word on yellow, comic onomatopoeia, lo-fi bed + loud mechanical foley.

## Workflow

1. **Research** 2-4 reliable sources (encyclopedias, museums, universities, journals, reputable
   science press quoting a named expert). Note disagreements; hedge with "sekitar"/"±" or drop the
   number. Keep source names for `upload.txt`.
2. **Script**: 8-10 scenes, 85-105 words, formula in `format.md` (hook → anchor → mechanism →
   twist → closer) shaped by the gaya's recipe in `genres.md` (hook type, order, tone, voice speed). One idea + one picture per scene. Show the user the numbered script unless they
   said to just go.
3. **Project**: `projects/<slug>/storyboard.json` with `genre` (the gaya), `style` (the look), `music`
   when the gaya overrides the look's bed (misteri → `lukis`), per-scene `id`, `narration`
   (digits), `spoken` (numbers written out; delivery punctuation "…"), `keywords` (1-2), `sfx`
   cues, `camera`, optional `effects`, `transition`, `chrome` (hud), `paint` (lukis: scene, flash/blast
   words, scary — see `styles/lukis/guide.md`).
4. **Voice** (decides all timing):
   ```bash
   python scripts/voice.py projects/<slug>            # OmniVoice per scene + Whisper word times
   python scripts/build_timeline.py projects/<slug>
   ```
   Target 35-47 s (55-62 s if the user asked for ~1 minute, see `format.md`). Too long →
   `voice.py --align-only --speed 1.12` (re-uses clips) or trim words / "…" pauses.
   Whisper aligns each scene clip on its own, so every word lands in its scene.
   Redo one scene: `voice.py --only s04`. If OmniVoice is unreachable, say so; `build_timeline.py`
   then estimates timing and the video can be rendered silent.
   **Real objects first (bedah, and any video that shows real devices, appliances or buildings)**: before
   modelling, research how the things really look and how they are really installed. Run
   `python scripts/refs.py projects/<slug> "item=query1;query2" ...` (Wikimedia Commons photos + contact
   sheets in `projects/<slug>/refs/`), look at every sheet, read how the system is installed in Indonesia
   (PLN/PUIL/manufacturer material), and write `refs/SPEK.md`: per object the real size in metres,
   colours, visible parts, where and how high it is mounted, and the real wiring/plumbing route. Model from
   the spec, check each object in a small gallery render next to its photo, then build the scenes.
   Reuse `styles/bedah/lib/40-listrik.js` (household electrical equipment) and `30-rumah.js` (house).
5. **Scenes**: write `projects/<slug>/gen_scenes.py` that imports `svgkit`, the style `kit.py` and
   `timing.Timing`, writes `scenes/sNN.svg`, and writes each scene's `texts` (titles/stats/tags)
   back into the storyboard. Time every story action to its word with `T.at(sid, "word")`.
   Spend the effort here: full frame, big subject, 4+ ambient motions, one story action per
   scene on its word, a camera move. Draw the topic-specific subject by hand at kit quality.
   **bedah** needs no scene art either: write `projects/<slug>/model.js` (the 3D object, cut, shots,
   callouts, glows, readout; contract in `styles/bedah/guide.md`, templates `projects/termos-bedah/`
   (toon, one object), `projects/listrik-rumah-aman/` (clay, house built up, `BEDAH.rumah`) and
   `projects/lift-bongkar/` (clay, machine built up, building section `BEDAH.gedung`, sepia flashback)),
   and `gen_scenes.py` writes empty SVGs + one beat title per scene + `bunyi` words.
   **lukis** needs no scene art: `gen_scenes.py` only writes empty SVGs + `texts`; the painting comes
   from `storyboard.paint` and per-scene `paint` segments (volcano, twilight town/fjord/beach, globe). Put
   flashes/blasts/waves on the shock words.
6. **Preview**: `python scripts/render.py projects/<slug> --stills` → look at
   `stills/contact_sheet.png` and 2-3 full stills; `--at 3.1 3.6` to check an action. Fix, repeat.
7. **Sound**: `python scripts/sound.py projects/<slug>` (SFX from the cues + the style's music bed).
   Real recordings (e.g. from the myinstants-sfx skill) go in `audio/sfx_src/` and play through
   `{"kind": "file", "src": "audio/sfx_src/x.mp3", "word": ..., "lp": 2500}` cues; note their source,
   since meme/user-uploaded clips may not be safe for monetized videos.
8. **Render**: `python scripts/render.py projects/<slug>` (≈3-6 min for 40 s; run in background,
   10-min timeout). Then pull 3-4 frames with ffmpeg and check loudness ≈ -14 LUFS
   (`ffmpeg -i video.mp4 -af ebur128 -f null -`). Audio-only changes: `render.py --remux`.
   **lukis** can render with HyperFrames instead (same paint.js, same frame, ~2.4x faster, needs
   internet + Node): `python scripts/hyperframes.py projects/<slug> --render` → builds `hf/`, runs
   `hyperframes check` (must report 0 errors), renders `video-hf.mp4` with the mixed audio at -14 LUFS.
   Live scrubbing: `cd projects/<slug>/hf && npx --yes hyperframes@0.8.191 preview`.
9. **Upload text**: `upload.txt` per `format.md` §5 (title ≤ 60 chars + #shorts, hook line,
   2-4 fact sentences, a question, `Sumber:` line, AI disclosure line, hashtags).
10. Reply briefly: title, duration, gaya + look, voice, what you hedged, the file paths.

## Rules

- Original scripts and art only. Never copy another channel's video, name, logo or watermark.
  Matching a *format and look* is fine; reproducing a specific video is not.
- Facts first: every number in the video must be in a source you read.
- Keep the YouTube safe zone: important things between y 260 and y 1640; captions at
  `caption_y` (1420-1440); nothing important in the right 140 px.
- Everything visible is a pure function of time (the engine seeks frames). No random without
  a seed; kits are seeded.
- Scary mode is for events that really were deadly (eruptions, tsunamis); keep the narration factual
  and calm, let picture and sound carry the dread. Never use it for jokes or living victims.
- Misteri: label every theory as a theory; never present myths or conspiracies as fact.
- Bedah: the turn is "Kok bisa? Kita cek rahasianya." (except the "Ini namanya…" series variant, which
  ends each beat on "… ini namanya X" instead) and the last scene is always the CTA
  "Mau dicek rahasia apa lagi? Tulis di kolom komentar." (`genres.md` §bedah). In the series "Bongkar" (a
  machine built up step by step) the closer is "Habis ini kita mau cek rahasia apa? Tulis di kolom komentar."
  instead — never two questions in a row. The upload text asks the same question.
- New look ideas go into the look pack (css/overlay/kit), not into one video, so later videos
  inherit them. A new look = a new folder under `styles/` with the same files. A new gaya = a new
  section in `genres.md` (and a row in the table above), mapped to an existing or new look.
