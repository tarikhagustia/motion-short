# Gaya video (genre)

The user picks a **gaya** (what kind of video it is). The gaya decides the script shape, the narration
tone, the rhythm, the sound, and which **tampilan** (look pack in `styles/`) to use. The look packs are
an implementation detail; talk to the user in terms of gaya.

Write both into the storyboard: `"genre": "misteri"` (the gaya) and `"style": "emas"` (the look).

| Gaya | Untuk topik | Tampilan | Rasa |
|---|---|---|---|
| `dokumenter` | peristiwa nyata yang dramatis: bencana, letusan, badai, penjelajahan, alam liar | `lukis` (painted) · `emas` if the subject can't be painted yet | sinematik, tenang, berwibawa |
| `sains` | "bagaimana kalau…", luar angkasa, fisika, Bumi, angka besar, simulasi | `hud` | cepat, data, angka bergerak |
| `misteri` | fenomena belum terjelaskan, legenda, tempat hilang, sinyal aneh | `emas` with `night_cloth` grounds · `lukis` + `scary` for a natural event | gelap, pelan, penuh tanya |
| `explainer` | "kenapa…?", hewan, tubuh, makanan, sains sehari-hari | `buku` | hangat, ramah, jelas langkah demi langkah |
| `sejarah` | kerajaan, tokoh, pelayaran, budaya, arkeologi | `emas` | megah, kronologis, tanggal & nama |

All five keep the skeleton in `format.md` (hook → anchor → mechanism → twist → closer, 85-105 words,
35-47 s). Below is what changes per gaya.

---

## dokumenter

- **Hook**: drop the viewer into a moment, with time and place. "Pagi 26 Desember 2004, laut di Aceh
  tiba-tiba surut." Not a question.
- **Shape**: strict chronology: sebelum → saat → sesudah → dampak hari ini. The twist is a human or
  scale detail ("abunya sampai ke Eropa").
- **Narration**: calm, low, full sentences; never hype words ("gila", "wow"). `voice.py --speed 1.0`.
- **Rhythm**: fewer, longer scenes (7-8 × 5-6 s), slow camera pushes, `transition: "cut"` only on the
  event itself. Titles only for date, place, name.
- **Sound**: ambience leads (ocean, wind, fire, rumble), music low (`lukis`). For deadly events set
  `paint.scary: true` with blasts on the shock words (see `styles/lukis/guide.md`).
- **Closer**: what it changed / what remains today. Quiet.

## sains

- **Hook**: "Bagaimana kalau…?" or one impossible-sounding number. "Kalau Bumi berhenti berputar 1
  detik saja…"
- **Shape**: setup → rule of physics → step-by-step consequence with numbers → twist (the surprising
  scale or the reassuring truth).
- **Narration**: crisp, confident, numbers stated clearly. `--speed 1.05-1.1`.
- **Rhythm**: 9-10 short scenes (3-4 s), a counting readout or meter in most scenes, chrome `status`
  changes every beat.
- **Sound**: beeps, data, scan, glitch on the shock; `hud` synth bed.
- **Closer**: back to safety: "Untungnya…" + the real-world number.

## misteri

- **Hook**: the unexplained fact, stated plainly. "Tahun 1977, teleskop menangkap sinyal 72 detik.
  Sampai sekarang tak ada yang tahu asalnya."
- **Shape**: the strange fact → what is known for sure → 2-3 explanations people proposed (each one
  "tapi…" knocked down or left open) → what is still unknown. Separate fact from theory in every
  sentence ("menurut legenda…", "sebagian peneliti menduga…").
- **Narration**: slow, hushed, with "…" pauses before the reveal. `--speed 0.95-1.0`.
- **Rhythm**: 8-9 scenes, slow pushes, dark grounds, one thing moving in the dark (light, fog, stars);
  fade transitions, a `cut` to black once.
- **Sound**: drone + heartbeat or a single low tone, sparse SFX, music `lukis` (dark pad) even on
  `emas`. Natural events can use `lukis` + `scary`.
- **Closer**: leave the question open and turn it to the viewer. "Menurutmu, apa yang sebenarnya terjadi?"
- **Honesty**: never present a myth, conspiracy, or unproven theory as fact; no invented witnesses or
  quotes. If sources say it is solved, say so; that is the twist.
- **Natural events** (eruptions, strange skies, tsunamis): `lukis` with per-scene painters, e.g.
  twilight → globe → volcano → fjord (see `styles/lukis/guide.md`). Voice `--gap 0.35-0.4`.

## explainer

- **Hook**: the everyday "kenapa?" or a cute surprising fact. "Kenapa kucing selalu jatuh dengan kaki
  duluan?"
- **Shape**: question → the short answer → how it works in 2-3 visual steps → a fun extra fact →
  callback to the viewer's life.
- **Narration**: warm, friendly, "kamu", simple words, one idea per sentence. `--speed 1.0-1.05`.
- **Rhythm**: 9 scenes, characters with expressions, a callout / lens / diagram per step, pop-in titles.
- **Sound**: pop, bubbles, scribble, page; `buku` music-box bed.
- **Closer**: a light, smiling line.

## sejarah

- **Hook**: a big claim about the past. "Seribu tahun lalu, kerajaan dari Sumatra menguasai jalur laut Asia."
- **Shape**: anchor (name, year, place) → rise → peak (one vivid detail: a ship, a temple, a trade good)
  → fall or mystery → legacy today.
- **Narration**: proud, measured, dates and names said clearly. `--speed 1.0`.
- **Rhythm**: 9 scenes, maps/routes, a stat card with the year, figures in rows, ornate frames.
- **Sound**: gong, chime, shimmer, `emas` gamelan bed.
- **Closer**: the trace that is still here ("namanya masih kita pakai sampai sekarang").
- **Honesty**: dates disputed between sources → "sekitar" or "abad ke-7".

---

## Asking the user

Ask before research, unless the user already named a gaya, a reference video, or said to just go
(then pick the best fit and say which). Use `AskUserQuestion` (one question, max 4 options):

- Rank the five by fit for the topic; offer the best 4, best first with "(Recommended)". The 5th stays
  reachable through the automatic "Other" field; name it in the question text.
- Each option: label = the gaya name ("Dokumenter"), description = one line of what *this* topic would
  look and sound like in that gaya ("Lukisan minyak hidup, narasi tenang, kronologis dari pagi hingga
  tsunami").
- Add a second question only when it changes the video: for a deadly event in `dokumenter` /
  `misteri`, ask the intensity: "Normal" vs "Seram (guncangan, abu, detak jantung)".

Without the tool, ask the same thing in one short message with a numbered list.
