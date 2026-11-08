// LUKIS: the painting lives on #paint and is redrawn every frame by paint.js (window.Paint).
// DATA.paint is already resolved by scripts/sound.py paint_config() (word lists -> seconds,
// per-scene `paint` -> a `sequence` of segments), so picture and sound always hit together.
(function () {
  const cfg = Object.assign({ scene: 'volcano', seed: 7 }, DATA.paint || {});
  const painter = Paint[cfg.scene](document.getElementById('paint'), Object.assign({ duration: DATA.timeline.duration }, cfg));
  // scary: red-orange title/keywords (style.css .scary) and text that shakes with the blasts
  const shakeEls = cfg.scary ? [document.getElementById('titles'), document.getElementById('caption')] : [];
  if (cfg.scary) document.getElementById('stage').classList.add('scary');
  const h = n => { const v = Math.sin(n * 127.1) * 43758.5453; return v - Math.floor(v); };
  const noise1 = x => { const i = Math.floor(x), f = x - i; return h(i) + (h(i + 1) - h(i)) * f * f * (3 - 2 * f); };
  STYLE.frame = function (t) {
    painter.render(t);
    if (!shakeEls.length) return;
    const a = 1.5 + (painter.shakeAt ? painter.shakeAt(t) : 0) * 22;
    const x = (noise1(t * 36) - .5) * 2 * a, y = (noise1(t * 41 + 9) - .5) * 2 * a;
    shakeEls.forEach(el => { el.style.translate = `${x.toFixed(1)}px ${y.toFixed(1)}px`; });
  };
})();
