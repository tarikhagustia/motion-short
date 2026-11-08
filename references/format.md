# Format: what makes these Shorts work

Derived from 15 reference Shorts (Indonesian fact Shorts, 32-47 s, 1080x1920, 30 fps, ≈ -15 LUFS).
Every one follows the same skeleton; the gaya (`genres.md`) bends the hook, order, tone and rhythm,
and the look pack changes the drawing.

## 1. Script

- **85-105 spoken words, 8-10 scenes, 3-6 s each, total 35-47 s.**
- **Panjang** (only when the user asks for about a minute): 120-150 words, 12-14 scenes, 55-62 s. Same
  skeleton with a fuller middle (two beats of mechanism, two of twist). Change place/picture more
  often so the minute never sits still.
- Indonesian, conversational but precise. Short clauses; commas where the voice should breathe.
- One idea + one picture per scene. If a scene needs two pictures, split it.

Skeleton:

1. **Hook (s01)** — the strange claim or a question, never background.
   "Ada hewan laut yang punya tiga jantung sekaligus." / "Bagaimana kalau Matahari tiba-tiba lenyap?"
2. **Anchor (1-2 scenes)** — name, place, number, year. "Namanya Madagaskar, lebih dari 6.000 km dari Nusantara."
3. **Mechanism / story (3-4 scenes)** — cause → event → consequence, concrete and visual.
4. **Twist (1-2 scenes)** — "Anehnya…", "Tapi…", the counter-intuitive bit, or honest uncertainty
   ("Ilmuwan belum tahu pasti…").
5. **Closer (1 scene)** — an image-like summary or a link to the viewer's life; often a warm/relieving line.

`narration` uses digits ("6.000 km", "±1.200", "8 menit 20 detik"); `spoken` writes them out
("enam ribu kilometer"). Same words in the same order otherwise, because caption words are matched to
the voice. Use "…" in `spoken` for a held pause. OmniVoice ignores `[tags]`; they are stripped.

## 2. Scene rhythm (what the reference editors do)

- Every scene has **one story action on its key word** (a number counts up, a route draws, a heart
  pops, the screen goes dark on "gelap"). Get the time from `T.at(sid, "word")`.
- **Ambient life everywhere**: 4+ things moving (waves drifting, palms swaying, stars twinkling,
  rings spinning, bubbles rising, eyes blinking).
- **Camera**: slow push-in or pull-out every scene; alternate directions. `transition: "cut"` only for
  a shock beat (darkness, explosion).
- **Shot variety**: in 9 scenes use at least 5 shot types — establishing, map/route, close-up object,
  diagram/cross-section, character reaction, big-number card, crowd/rows, comparison.
- **Titles**: not on every scene. Use one for the hook, names, and every key number (stat with a
  `sub` label). Titles appear on their word, not at scene start.

## 3. On-screen text

- **Title** (top, y 180-430): a name, a short phrase, or a question. Max ~14 characters per line.
- **Stat**: the key number, huge, with `sub` (e.g. "TAHUN LALU", "SETIAP HARI") and optional `unit`.
- **Tag**: a location / label strip under a title.
- **Captions** (bottom, automatic): 2-5 words per page, spoken words bright, future words dim,
  `keywords` in the accent colour. Choose 1-2 keywords per scene: the number and the surprising word.

## 4. Sound

- Voice: one take per scene, joined with ~0.28 s gaps (voice.py).
- SFX cue per story action (on its word) + one quiet ambience bed per scene + automatic soft whoosh
  on cross-faded scene changes.
- Music bed from the style (sound.py), ducked under the voice. Final mix normalised to -14 LUFS.

## 5. Upload text (`upload.txt`)

```
JUDUL:
<Subjek>: <hook singkat> #shorts            (≤ 60 karakter sebelum #shorts)

DESKRIPSI:
<Kalimat hook> <1 emoji>
<2-4 kalimat fakta inti dengan angka dan tahun.>
<Satu pertanyaan ke penonton> 👇

Sumber: <Penerbit "Judul">; <Penulis dkk. Tahun, Jurnal>.

Animasi, narasi, musik, dan efek suara dibuat dengan bantuan AI.

#<topik> #<topik2> #<daerah/bidang> #faktaunik #edukasi #shorts
```
