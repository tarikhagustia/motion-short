# Motion Shorts

Skill [Claude Code](https://claude.com/claude-code) untuk membuat **video fakta pendek berbahasa Indonesia**
(YouTube Shorts / Reels / TikTok, 9:16, 35–47 detik) yang siap upload: naskah hasil riset dengan sumber,
narasi suara kloning (OmniVoice), caption karaoke per kata, adegan animasi, SFX + musik latar, dan teks upload.

Cukup beri topik — misalnya *"buatin shorts tentang letusan Tambora"* — Claude akan menanyakan gaya video,
lalu mengerjakan semuanya sampai `video.mp4` dan `upload.txt` jadi.

## Gaya video

| Gaya | Tampilan | Cocok untuk |
|---|---|---|
| **dokumenter** | `lukis` — lukisan cat minyak hidup (asap, api, petir), opsi mode *seram* | bencana, peristiwa dramatis, alam |
| **sains** | `hud` — layar gelap, neon cyan/oranye, panel & meter | "bagaimana kalau…", luar angkasa, fisika |
| **misteri** | `emas` versi malam + suara gelap | hal yang belum terjelaskan, legenda |
| **explainer** | `buku` — kertas cat air, karakter pensil lucu | "kenapa…?", hewan, tubuh, sains sehari-hari |
| **sejarah** | `emas` — kain batik + garis emas + gamelan | kerajaan, tokoh, budaya |
| **bedah** | `bedah` — model 3D toon dibelah (Three.js), bagian yang dibahas jadi kuning, header angka + badge | "kok bisa?" benda sehari-hari: magic com, presto, meteran, MCB, motor matic |

## Cara kerja

Semua dirender lokal dan deterministik: SVG per adegan + template HTML berbasis waktu, ditangkap frame demi
frame dengan Playwright, lalu digabung dengan ffmpeg.

```
topik → riset & naskah → storyboard.json → voice.py (OmniVoice + Whisper)
      → build_timeline.py → gen_scenes.py → render.py --stills (preview)
      → sound.py → render.py → video.mp4 + upload.txt
```

## Instalasi

1. Salin folder ini ke direktori skill Claude Code:
   ```bash
   git clone https://github.com/tarikhagustia/motion-short.git ~/.claude/skills/motion-shorts
   ```
2. Pasang dependensi:
   ```bash
   pip install numpy scipy pillow faster-whisper playwright
   playwright install chromium
   ```
   Juga butuh **ffmpeg** di PATH. Untuk render HyperFrames (gaya `lukis`, ~2,4× lebih cepat) butuh **Node.js** dan internet.
3. Atur server TTS OmniVoice (API gaya OpenAI `/v1/audio/speech`) lewat environment variable:

   | Variabel | Isi |
   |---|---|
   | `OMNIVOICE_URL` | endpoint API, mis. `http://host:7000/v1/audio/speech` |
   | `OMNIVOICE_MODEL` | nama model |
   | `OMNIVOICE_REF_AUDIO` | path sampel suara **di server** TTS |
   | `OMNIVOICE_REF_TEXT` | transkrip sampel suara tersebut |
   | `OMNIVOICE_LANG` | bahasa, default `indonesian` |

   Kalau OmniVoice tidak bisa dijangkau, timing diestimasi dan video tetap bisa dirender tanpa suara.

## Penggunaan

Di Claude Code, minta saja:

> buatin video fakta 40 detik tentang gurita punya tiga jantung

Atau jalankan script secara manual per proyek (`projects/<slug>/`):

```bash
python scripts/voice.py projects/<slug>            # narasi + timing kata
python scripts/build_timeline.py projects/<slug>
python projects/<slug>/gen_scenes.py               # gambar adegan
python scripts/render.py projects/<slug> --stills  # preview contact sheet
python scripts/sound.py projects/<slug>            # SFX + musik
python scripts/render.py projects/<slug>           # video final
```

Detail lengkap ada di [SKILL.md](SKILL.md), [references/format.md](references/format.md),
[references/genres.md](references/genres.md), [references/engine.md](references/engine.md) dan
`styles/<tampilan>/guide.md`.

## Struktur

```
├── SKILL.md            instruksi skill untuk Claude
├── assets/             template.html (engine animasi), font, simbol
├── scripts/            voice, timeline, render, sound, svgkit, hyperframes, klien OmniVoice
├── styles/             paket tampilan: emas, buku, hud, lukis, bedah
└── references/         format naskah, gaya video, dokumentasi engine
```

## Aturan konten

- Naskah dan gambar orisinal. Meniru *format dan tampilan* boleh; menyalin video, nama, logo, atau watermark channel lain tidak.
- Setiap angka di video harus berasal dari sumber yang dibaca; sumber dicantumkan di `upload.txt`.
- Teori dan mitos selalu diberi label sebagai teori.

## Lisensi font

Semua font di `assets/fonts/` berlisensi [SIL Open Font License](assets/fonts/OFL.txt).
