# Style: buku (warm storybook)

For animals, the body, food, everyday "kenapa?" science, cute surprising facts.
Reference feel: "Kotoran wombat berbentuk kubus", "Bunglon ganti warna".

## Look

- **Ground**: cream watercolour paper (`paper_bg`), soft `sky_wash`, `underwater_bg` with light rays.
- **Characters**: round and friendly, flat muted colours, ~3 px dark-brown pencil outline (`INK #4b3427`),
  dot `eyes()` that blink, `blush()`, small highlight blobs. A `wc_circle` (watercolour disc) behind
  the main character, like a vignette.
- **Palette**: coral `#e98a6c`, mint `#bcd8c9`, sage, sea `#7fb0b8`, mustard, pink, cream; accent red-orange `#d4552b`.
- **Titles**: Fredoka SemiBold brown/red with a cream offset, `pop` animation (letters bounce in).
- **Captions**: cream pill, Fredoka, dark-brown text, keywords red-orange.
- **Labels**: `callout()` (dotted pointer + label), `label_hand()`, `tag` class `small` for section labels.
- **Music**: music-box waltz (`music: "buku"`).

## Kit (`kit.py`)

backgrounds `paper_bg`, `sky_wash`, `soft_clouds`, `ground_strata`, `underwater_bg` · nature `bush`,
`grass_tufts`, `seaweed`, `rock`, `bubbles_rise` · characters `scientist(pose=think|point|wow|calm)`,
`eyes`, `blush` · props `thought_bubble`, `question`, `sparkle`, `heart`, `medal`, `sunburst`, `lens`
(circular zoom-in/cross-section) · labels `callout`, `label_hand` · helpers `wobble_path`, `blob_path`.

Draw the topic animal by hand in the project's `gen_scenes.py` (see the octopus in
`projects/gurita-tiga-jantung`): thick round-capped stroked limbs with an ink outline underneath,
a big rounded head, eyes high, blush, sway on every limb.

## Shot ideas

- Hook: watercolour disc + icons popping in on the number ("3 jantung?").
- Character reveal: animal pops in, title on its name, a prop (lightbulb, sparkle) on the adjective.
- Inside view: big cut-away body outline with organs + `callout`s, flowing dots along vessels.
- Scientist reaction: `scientist("think")` + `thought_bubble` with the puzzle inside.
- Before/after or cause/effect: monitor line going flat, arrows in/out, "sembur!" labels.
- Closer: the character doing the "answer" in a calm scene, small joke prop (sunglasses).
