/* paint.js — painterly (oil / brush-stroke) renderer for the `lukis` style.
 *
 * Engine-agnostic: works inside the motion-shorts template (STYLE.frame) and inside a HyperFrames
 * composition (hf-seek). Everything drawn is a pure function of time t, all randomness is seeded.
 *
 *   const P = Paint.volcano(canvas, { seed: 7, flashes: [1.6, 4.3, 7.8], duration: 10 });
 *   P.render(t);
 *
 * Scenes: volcano (eruption, blasts, tsunami waves), twilight (red / nacreous sky over a town or a
 * fjord), globe (painted Earth, pressure-wave rings, ash veil), sequence (one painter per segment,
 * crossfades, shared post pass). Every painter returns {render(t), flashes, shakeAt(t)}.
 *
 * Technique
 *  - Static backdrop painted ONCE into an offscreen canvas: a colour field (sky, islands, cone, sea)
 *    is sampled by tens of thousands of short multi-bristle strokes that follow a flow field
 *    (swirls in the sky, slope direction on the cone, horizontal on the sea).
 *  - Per frame: camera push, crater glow, flowing lava, sea reflections, a swirling smoke column
 *    made of brush dabs (lit orange from below), ember streaks, procedural lightning with glow.
 */
(function () {
  const W = 1080, H = 1920;

  // ---------------------------------------------------------------- seeded helpers
  function rng(seed) { let s = (Math.imul(seed | 0, 2654435761) ^ 0x9e3779b9) >>> 0 || 1; for (let i = 0; i < 3; i++) s = (s * 1664525 + 1013904223) >>> 0; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }
  function hash(i, j, seed) { let h = (i * 374761393 + j * 668265263 + seed * 2147483647) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
  function vnoise(x, y, seed) {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const a = hash(xi, yi, seed), b = hash(xi + 1, yi, seed), c = hash(xi, yi + 1, seed), d = hash(xi + 1, yi + 1, seed);
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  }
  function fbm(x, y, seed, oct = 4) { let s = 0, a = .5, f = 1; for (let o = 0; o < oct; o++) { s += a * vnoise(x * f, y * f, seed + o * 17); f *= 2; a *= .5; } return s; }
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const smooth = (a, b, x) => { const k = clamp((x - a) / (b - a), 0, 1); return k * k * (3 - 2 * k); };
  const hex = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  const mix = (c1, c2, k) => [lerp(c1[0], c2[0], k), lerp(c1[1], c2[1], k), lerp(c1[2], c2[2], k)];
  const css = (c, a = 1) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;

  // ---------------------------------------------------------------- generic brush stroke
  // A stroke = a few parallel "bristles" along a slightly curved path, colour-jittered per bristle.
  function stroke(g, x, y, ang, len, wid, col, alpha, r, curve = 0) {
    const ca = Math.cos(ang), sa = Math.sin(ang), nx = -sa, ny = ca;
    const n = 3 + (wid > 6 ? 1 : 0);
    for (let b = 0; b < n; b++) {
      const off = (b / (n - 1) - .5) * wid;
      const jit = (r() - .5) * 26;
      const c = [col[0] + jit, col[1] + jit * .9, col[2] + jit * .8];
      const x0 = x - ca * len / 2 + nx * off, y0 = y - sa * len / 2 + ny * off;
      const x1 = x + ca * len / 2 + nx * off, y1 = y + sa * len / 2 + ny * off;
      g.strokeStyle = css(c, alpha * (.55 + r() * .45));
      g.lineWidth = wid / n * (1.3 + r() * .7);
      g.beginPath(); g.moveTo(x0, y0);
      g.quadraticCurveTo(x + nx * (off + curve * len), y + ny * (off + curve * len), x1, y1);
      g.stroke();
    }
  }

  // A smeared paint dab: one wide soft body + two thin bristle highlights (blends like wet paint).
  function smear(g, x, y, ang, len, wid, col, alpha, r, curve = 0) {
    const ca = Math.cos(ang), sa = Math.sin(ang), nx = -sa, ny = ca;
    const x0 = x - ca * len / 2, y0 = y - sa * len / 2, x1 = x + ca * len / 2, y1 = y + sa * len / 2;
    const cx = x + nx * curve * len, cy = y + ny * curve * len;
    g.strokeStyle = css(col, alpha * .8); g.lineWidth = wid;
    g.beginPath(); g.moveTo(x0, y0); g.quadraticCurveTo(cx, cy, x1, y1); g.stroke();
    for (let b = -1; b <= 1; b += 2) {
      const j = (r() - .5) * 34, off = b * wid * .28;
      g.strokeStyle = css([col[0] + j + 18 * b, col[1] + j + 14 * b, col[2] + j + 12 * b], alpha * .55); g.lineWidth = wid * .22;
      g.beginPath(); g.moveTo(x0 + nx * off, y0 + ny * off); g.quadraticCurveTo(cx + nx * off, cy + ny * off, x1 + nx * off, y1 + ny * off); g.stroke();
    }
  }

  // ---------------------------------------------------------------- shared finishing pass
  // Ash fall, a darkening cold grade and the vignette (red, pulsing on a 0.92 s heartbeat when scary).
  // Screen space. Pure function of t. o.ashAmt 0..1 fades the ash (0 = none).
  const ASH = (() => { const r = rng(916); return Array.from({ length: 320 }, (_, i) => ({ x: r() * W, y: r() * H, vx: 30 + r() * 60, vy: 70 + r() * 120, s: i < 40 ? 4 + r() * 5 : 1.2 + r() * 2.4, ph: r() * 6, fg: i < 40 })); })();
  const heartbeat = t => { const p = ((t % .92) + .92) % .92; return Math.exp(-((p / .07) ** 2)) + .6 * Math.exp(-(((p - .22) / .07) ** 2)); };
  function post(g, t, o = {}) {
    const scary = !!o.scary, duration = o.duration ?? 10, ashA = o.ashAmt ?? 1, ash = o.ash ?? ASH;
    g.setTransform(1, 0, 0, 1, 0, 0);
    if (scary) {
      if (ashA > .01) for (const p of ash) {           // ash fall: fine flecks + a few big blurred foreground flakes
        const x = ((p.x + p.vx * t + Math.sin(t * 1.3 + p.ph) * 18) % (W + 40) + W + 40) % (W + 40) - 20;
        const y = ((p.y + p.vy * t * (p.fg ? 1.6 : 1)) % (H + 40) + H + 40) % (H + 40) - 20;
        g.fillStyle = p.fg ? `rgba(60,52,56,${.55 * ashA})` : `rgba(150,138,140,${.45 * ashA})`;
        if (p.fg) { g.filter = 'blur(2px)'; }
        g.beginPath(); g.ellipse(x, y, p.s, p.s * .7, p.ph, 0, Math.PI * 2); g.fill();
        if (p.fg) g.filter = 'none';
      }
      const k2 = clamp(t / duration, 0, 1);          // grade that deepens over time: a little darker and colder
      g.globalCompositeOperation = 'multiply';
      g.fillStyle = `rgb(${225 - 20 * k2 | 0},${205 - 35 * k2 | 0},${210 - 30 * k2 | 0})`; g.fillRect(0, 0, W, H);
      g.globalCompositeOperation = 'source-over';
    }
    const hb = scary ? heartbeat(t) : 0;
    const vg = g.createRadialGradient(W / 2, H * .46, H * (.25 - hb * .04), W / 2, H * .46, H * .75);
    vg.addColorStop(0, 'rgba(0,0,0,0)');
    vg.addColorStop(1, scary ? `rgba(${50 + hb * 60 | 0},0,4,${.72 + hb * .15})` : 'rgba(8,4,10,.6)');
    g.fillStyle = vg; g.fillRect(0, 0, W, H);
  }

  // ---------------------------------------------------------------- the volcano scene
  function volcano(canvas, opt = {}) {
    const seed = opt.seed ?? 7;
    const g = canvas.getContext('2d');
    const CX = opt.cx ?? 540, HORIZON = opt.horizon ?? 1180, PEAK = opt.peak ?? 880;
    const CONE_W = opt.coneW ?? 300;          // half width at the waterline
    const CRATER = [CX, PEAK + 10];
    const flashes = opt.flashes ?? [1.6, 4.4, 7.6];
    const duration = opt.duration ?? 10;
    const zoom = opt.zoom ?? [1.0, 1.08];
    const ramp = opt.ramp ?? [1, 1];                  // eruption strength at start / end
    const intensity = typeof opt.intensity === 'function' ? opt.intensity : (t => lerp(ramp[0], ramp[1], clamp(t / duration, 0, 1)));
    const scary = !!opt.scary;                         // tremor, ash fall, red heartbeat vignette, grade
    const blasts = opt.blasts ?? [];                   // big explosions: shake, flash, shockwave, lava bombs

    const PAL = {
      skyTop: hex('#1d1a33'), skyMid: hex('#4a2b45'), skyLow: hex('#b3532c'), glow: hex('#f29a45'),
      sea: hex('#141b2c'), seaHi: hex('#2b3550'), island: hex('#2a1f2b'), islandHi: hex('#4a3240'),
      cone: hex('#3a2320'), coneHi: hex('#6e3a28'), lavaLit: hex('#c8582a'),
    };

    // shapes
    const rakata = x => 1180 - Math.max(0, 330 - Math.abs(x - 120) * 1.25) - (x < 220 ? 120 * smooth(220, 0, x) : 0);
    const sertung = x => 1180 - Math.max(0, 90 - Math.abs(x - 960) * .5);
    const coneTop = x => { const d = Math.abs(x - CX) * (x < CX ? 1 : .92); if (d > CONE_W) return 1e9; const k = d / CONE_W; return PEAK + (HORIZON - PEAK) * Math.pow(k, 1.25) + (d < 50 ? (50 - d) * .45 : 0) + (fbm(x * .02, 1.7, seed + 40) - .5) * 26 * k; };

    function colorAt(x, y, r) {
      // sky
      if (y < HORIZON) {
        const k = y / HORIZON;
        let c = k < .55 ? mix(PAL.skyTop, PAL.skyMid, k / .55) : mix(PAL.skyMid, PAL.skyLow, (k - .55) / .45);
        const dg = Math.hypot(x - CX, (y - PEAK) * .8);
        c = mix(c, PAL.glow, clamp(1 - dg / 620, 0, 1) ** 2 * .8);
        c = mix(c, PAL.skyTop, (fbm(x * .004, y * .004, seed + 5) - .5) * .5 + .1);
        if (y > rakata(x)) c = mix(PAL.island, PAL.islandHi, clamp((x - 60) / 300, 0, 1) * .5 + fbm(x * .02, y * .02, seed) * .3);
        if (y > sertung(x)) c = mix(PAL.island, PAL.islandHi, .3);
        if (y > coneTop(x)) {
          const d = Math.abs(x - CX) / CONE_W;
          c = mix(PAL.coneHi, PAL.cone, d * .8 + (y - PEAK) / (HORIZON - PEAK) * .3);
          c = mix(c, PAL.lavaLit, clamp(1 - Math.hypot(x - CX, y - PEAK) / 260, 0, 1) * .8);
        }
        return c;
      }
      // sea
      const k = (y - HORIZON) / (H - HORIZON);
      let c = mix(PAL.seaHi, PAL.sea, Math.pow(k, .6));
      const refl = clamp(1 - Math.abs(x - CX) / (160 + k * 260), 0, 1) * (1 - k * .7);
      c = mix(c, PAL.glow, refl * .55);
      return c;
    }
    function angleAt(x, y) {
      if (y >= HORIZON) return (fbm(x * .01, y * .03, seed + 9) - .5) * .35;
      if (y > coneTop(x)) return x < CX ? Math.PI * .62 : Math.PI * .38;   // down the slope
      if (y > rakata(x) || y > sertung(x)) return Math.PI / 2 + (fbm(x * .01, y * .01, seed) - .5);
      // sky: swirls (curl-ish) + circular flow around the glow
      const dx = x - CX, dy = y - PEAK;
      const around = Math.atan2(dy, dx) + Math.PI / 2;
      const sw = fbm(x * .0035, y * .0035, seed + 3) * Math.PI * 4;
      const kk = clamp(1 - Math.hypot(dx, dy) / 700, 0, 1);
      return lerp(sw, around, kk * .7);
    }

    // ---- paint the backdrop once
    const bg = document.createElement('canvas'); bg.width = W; bg.height = H;
    const sm = document.createElement('canvas'); sm.width = W; sm.height = H; const sg = sm.getContext('2d');
    const bgg = bg.getContext('2d');
    (function paintBackdrop() {
      const r = rng(seed * 31 + 1);
      // under-paint (blurred colour field) so no canvas shows between strokes
      const step = 12;
      for (let y = 0; y < H; y += step) for (let x = 0; x < W; x += step) { bgg.fillStyle = css(colorAt(x, y, r)); bgg.fillRect(x, y, step, step); }
      bgg.filter = 'blur(10px)'; bgg.drawImage(bg, 0, 0); bgg.filter = 'none';
      bgg.lineCap = 'round';
      const passes = [[11, 34, 9, .55], [7, 22, 6, .7], [5, 14, 4, .8]];   // spacing, length, width, alpha
      passes.forEach(([sp, len, wid, al], pi) => {
        for (let y = -10; y < H + 10; y += sp) for (let x = -10; x < W + 10; x += sp) {
          const px = x + (r() - .5) * sp * 1.4, py = y + (r() - .5) * sp * 1.4;
          const ang = angleAt(px, py) + (r() - .5) * .35;
          stroke(bgg, px, py, ang, len * (.7 + r() * .6), wid, colorAt(px, py, r), al, r, (r() - .5) * .25);
        }
      });
      // a few bright rim strokes on the cone's lit side
      for (let i = 0; i < 900; i++) {
        const x = CX - CONE_W + r() * CONE_W * 2, top = coneTop(x); if (top > 1e8) continue;
        const y = top + r() * 40;
        stroke(bgg, x, y, angleAt(x, y + 5), 16, 3, mix(PAL.lavaLit, PAL.glow, r()), .35 * (1 - Math.abs(x - CX) / CONE_W), r);
      }
    })();

    // ---- lava rivulets (fixed paths down the slopes)
    const lava = [];
    (function () {
      const r = rng(seed + 77);
      for (let i = 0; i < 9; i++) {
        const side = i % 2 ? 1 : -1; let x = CX + side * (8 + r() * 20), y = PEAK + 18; const pts = [[x, y]];
        const target = .35 + r() * .55;
        let guard = 0; while (y < PEAK + (HORIZON - PEAK) * target && guard++ < 80) { x += side * (1 + r() * 7) + Math.sin(guard * .7 + i) * 4; y = Math.max(y + 10 + r() * 9, coneTop(x) + 10); pts.push([x + (r() - .5) * 10, y]); }
        lava.push({ pts, phase: r() * 10, w: 2.5 + r() * 3 });
      }
    })();

    // ---- smoke particles (static parameters; position is a function of t)
    const PUFFS = opt.puffs ?? 170, PER = opt.perPuff ?? 26, LIFE = 7.5;
    const puffs = [];
    (function () {
      const r = rng(seed + 101);
      const grey = ['#2f2b36', '#45404c', '#5a5360', '#6f6670', '#867c84'].map(hex);
      for (let i = 0; i < PUFFS; i++) {
        const pf = { ph: (i / PUFFS) * LIFE + r() * .3, th: r() * Math.PI * 2, w: .5 + r() * .8, rr: .6 + r() * .5, j: r(), hot: Math.pow(r(), 1.6), parts: [] };
        for (let k = 0; k < PER; k++) {
          const a = r() * Math.PI * 2, rad = Math.sqrt(r());
          pf.parts.push({ ox: Math.cos(a) * rad, oy: Math.sin(a) * rad * .75, c: grey[(r() * grey.length) | 0], s: r(), ang: (r() - .5) * 1.2, len: .7 + r() * .7, seedk: (r() * 1e6) | 0 });
        }
        puffs.push(pf);
      }
    })();
    const EMB_N = 170, ELIFE = 1.7;
    const embers = [];
    (function () { const r = rng(seed + 202); for (let i = 0; i < EMB_N; i++) embers.push({ ph: r() * ELIFE, vx: (r() - .5) * 560, vy: -(520 + r() * 520), x0: (r() - .5) * 50, c: r() }); })();

    // ---- lava bombs per blast, and ash flecks (static params)
    const bombs = blasts.map((_, bi) => { const r = rng(seed * 53 + bi * 17); return Array.from({ length: 28 }, () => ({ vx: (r() - .5) * 1100, vy: -(700 + r() * 800), rad: 5 + r() * 9, c: r() })); });
    const ash = (() => { const r = rng(seed + 909); return Array.from({ length: 320 }, (_, i) => ({ x: r() * W, y: r() * H, vx: 30 + r() * 60, vy: 70 + r() * 120, s: i < 40 ? 4 + r() * 5 : 1.2 + r() * 2.4, ph: r() * 6, fg: i < 40 })); })();
    const waves = opt.waves ?? [];                     // tsunami: a wall of water rolls from the horizon toward the viewer

    // ---- lightning paths, one per flash, built deterministically
    function bolt(idx) {
      const r = rng(seed * 997 + idx * 131);
      const x0 = CX + (r() - .5) * 220, y0 = 260 + r() * 160, x1 = CX + (r() - .5) * 90, y1 = PEAK - 60 - r() * 80;
      let pts = [[x0, y0], [x1, y1]];
      let disp = 120;
      for (let it = 0; it < 6; it++) {
        const np = [pts[0]];
        for (let k = 1; k < pts.length; k++) { const a = pts[k - 1], b = pts[k]; np.push([(a[0] + b[0]) / 2 + (r() - .5) * disp, (a[1] + b[1]) / 2 + (r() - .5) * disp * .25]); np.push(b); }
        pts = np; disp *= .55;
      }
      const branches = [];
      for (let b = 0; b < 2; b++) {
        const start = pts[(pts.length * (.25 + r() * .4)) | 0]; let bp = [start]; let [x, y] = start; const dir = r() < .5 ? -1 : 1;
        for (let k = 0; k < 7; k++) { x += dir * (14 + r() * 22); y += 10 + r() * 26; bp.push([x, y]); }
        branches.push(bp);
      }
      return { pts, branches };
    }
    const bolts = flashes.map((_, i) => bolt(i));
    function flashAmt(t) {   // returns [boltIndex, brightness 0..1]
      for (let i = 0; i < flashes.length; i++) {
        const a = t - flashes[i];
        if (a >= 0 && a < .42) { const on = (a < .07) || (a > .13 && a < .2) || (a > .27 && a < .36); return [i, on ? (a < .07 ? 1 : .75) : .12]; }
      }
      return [-1, 0];
    }

    function drawPath(pts) { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let k = 1; k < pts.length; k++) g.lineTo(pts[k][0], pts[k][1]); g.stroke(); }

    // ---- tsunami wave: the crest advances from the horizon to below the frame while it grows
    const foam = (() => { const r = rng(seed + 313); return Array.from({ length: 260 }, () => ({ u: r(), o: r(), l: r(), c: r() })); })();
    function drawWave(a, wi) {
      const D = 4.6; if (a < 0 || a > D) return;
      const q = a / D, e = q * q * (3 - 2 * q);
      const base = lerp(HORIZON + 30, H + 700, Math.pow(q, 1.6));          // where the wall meets the sea in front
      const hgt = lerp(40, 1250, Math.pow(q, .85));                          // wall height
      const crest = x => base - hgt * (1 + .12 * Math.sin(x * .006 + a * 1.7 + wi) + .08 * (vnoise(x * .004, a * .8, seed + 61) - .5));
      const gr = g.createLinearGradient(0, base - hgt * 1.15, 0, base);
      gr.addColorStop(0, 'rgba(60,80,92,.97)'); gr.addColorStop(.18, 'rgba(26,44,58,.98)'); gr.addColorStop(1, 'rgba(8,14,22,1)');
      g.fillStyle = gr; g.beginPath(); g.moveTo(-80, H + 600);
      for (let x = -80; x <= W + 80; x += 20) g.lineTo(x, crest(x));
      g.lineTo(W + 80, H + 600); g.closePath(); g.fill();
      g.lineCap = 'round';
      const r = rng(seed + 717 + wi * 31);                                   // fire-lit streaks on the face
      for (let i = 0; i < 220; i++) {
        const x = r() * (W + 160) - 80, top = crest(x), y = top + r() * hgt * .9;
        const lit = clamp(1 - Math.abs(x - CX) / 520, 0, 1) * (1 - (y - top) / (hgt + 1));
        stroke(g, x, y, Math.PI / 2 + (r() - .5) * .3, 30 + r() * 60, 6 + r() * 6, mix([24, 40, 54], [190, 96, 50], lit * .7), .35, r, (r() - .5) * .3);
      }
      for (const f of foam) {                                                // curling foam along the crest + spray
        const x = f.u * (W + 160) - 80, y = crest(x) + f.o * 26 - 8;
        const sz = (10 + f.l * 26) * (.5 + e);
        g.strokeStyle = `rgba(${200 + f.c * 40 | 0},${200 + f.c * 30 | 0},${210 + f.c * 30 | 0},${.75 * (1 - q * .4)})`;
        g.lineWidth = sz * .45; g.beginPath(); g.moveTo(x - sz, y); g.quadraticCurveTo(x, y - sz * .8, x + sz, y + sz * .2); g.stroke();
        const sp = a * 120 * f.l;
        g.fillStyle = `rgba(220,215,220,${.45 * (1 - q)})`; g.beginPath(); g.arc(x + (f.c - .5) * 60, y - sp - f.o * 40, 2 + f.l * 4, 0, Math.PI * 2); g.fill();
      }
    }
    const shakeAt = t => { let a = 0; for (const b of blasts) { const d = t - b; if (d >= 0 && d < 1.6) a += Math.exp(-d * 3.2); } for (const w of waves) { const d = t - w; if (d > 1.2 && d < 4.2) a += .35 * Math.sin(Math.PI * (d - 1.2) / 3); } return a; };

    // ---------------------------------------------------------------- per-frame render
    function render(t) {
      const r = rng(seed + ((t * 30) | 0) * 7);  // per-frame seeded jitter (deterministic)
      const I = intensity(t);
      const k = clamp(t / duration, 0, 1), e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      const z = lerp(zoom[0], zoom[1], e);
      g.setTransform(1, 0, 0, 1, 0, 0);
      g.globalCompositeOperation = 'source-over';
      g.fillStyle = '#0b0a12'; g.fillRect(0, 0, W, H);
      let amp = scary ? 2.2 * I : 0;
      for (const b of blasts) { const a = t - b; if (a >= 0 && a < 1.6) amp += 30 * Math.exp(-a * 3.2); }
      for (const w of waves) { const a = t - w; if (a > 1.2 && a < 4.2) amp += 10 * Math.sin(Math.PI * (a - 1.2) / 3); }
      const sx = (vnoise(t * 38, 1.3, seed) - .5) * 2 * amp, sy = (vnoise(t * 41, 7.7, seed) - .5) * 2 * amp;
      g.setTransform(z, 0, 0, z, CX - CX * z + sx, 1000 - 1000 * z + sy);
      g.drawImage(bg, 0, 0);
      if (scary) {   // darken only the painted sky, so the fire-lit column looms out of the dark
        const k3 = clamp(t / duration, 0, 1);
        const top = g.createLinearGradient(0, 0, 0, HORIZON);
        top.addColorStop(0, `rgba(6,3,8,${.86 + .1 * k3})`); top.addColorStop(.75, `rgba(6,3,8,${.45 + .15 * k3})`); top.addColorStop(1, 'rgba(6,3,8,.1)');
        g.fillStyle = top; g.fillRect(-60, -60, W + 120, HORIZON + 60);
        const sea = g.createLinearGradient(0, HORIZON, 0, H);
        sea.addColorStop(0, 'rgba(6,3,8,.2)'); sea.addColorStop(1, 'rgba(6,3,8,.7)');
        g.fillStyle = sea; g.fillRect(-60, HORIZON, W + 120, H - HORIZON + 60);
      }
      g.lineCap = 'round'; g.lineJoin = 'round';

      // crater glow (additive)
      const fl = .82 + .1 * Math.sin(t * 7.3) + .08 * Math.sin(t * 13.1 + 1);
      g.globalCompositeOperation = 'lighter';
      let gr = g.createRadialGradient(CRATER[0], CRATER[1], 0, CRATER[0], CRATER[1], 330);
      gr.addColorStop(0, `rgba(255,214,140,${.75 * fl * I})`); gr.addColorStop(.25, `rgba(255,140,60,${.4 * fl * I})`); gr.addColorStop(1, 'rgba(255,90,30,0)');
      g.fillStyle = gr; g.fillRect(CRATER[0] - 340, CRATER[1] - 340, 680, 680);

      // lava rivulets: glowing, with a slow flowing pulse
      lava.forEach(L => {
        g.strokeStyle = `rgba(255,120,40,${.35 * I})`; g.lineWidth = L.w * 3; drawPath(L.pts);
        g.strokeStyle = `rgba(255,190,90,${.8 * I})`; g.lineWidth = L.w; g.setLineDash([18, 14]); g.lineDashOffset = -(t * 40 + L.phase * 10); drawPath(L.pts); g.setLineDash([]);
      });

      // sea reflection shimmer
      g.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 70; i++) {
        const rr = rng(seed + 500 + i), yy = HORIZON + 20 + rr() * 520, spread = 70 + (yy - HORIZON) * .5;
        const xx = CX + (rr() - .5) * 2 * spread + Math.sin(t * (1 + rr()) + i) * 10;
        const a = (.12 + .18 * (.5 + .5 * Math.sin(t * 3 + i * 1.7))) * (1 - (yy - HORIZON) / 700) * I;
        g.strokeStyle = `rgba(255,${150 + rr() * 60 | 0},80,${a})`; g.lineWidth = 3 + rr() * 4;
        g.beginPath(); g.moveTo(xx - 20 - rr() * 30, yy); g.lineTo(xx + 20 + rr() * 30, yy + (rr() - .5) * 3); g.stroke();
      }
      g.globalCompositeOperation = 'source-over';

      // smoke column: billowing puffs swirl around a rising, leaning axis; back puffs first
      const list = [];
      for (const pf of puffs) {
        const a = ((t + pf.ph) % LIFE), q = a / LIFE;
        const h = Math.pow(q, .8) * (PEAK + 160);
        const R = (30 + h * .3 + Math.sin(h * .006) * 60) * pf.rr;
        const th = pf.th + a * .75 * pf.w;
        const lean = Math.pow(h / 1000, 2) * 150;
        const x = CRATER[0] + Math.cos(th) * R + lean + (fbm(h * .004, pf.j * 9, seed) - .5) * 70;
        const y = CRATER[1] - h;
        list.push({ pf, q, x, y, zf: Math.sin(th), th, h });
      }
      list.sort((a, b) => a.zf - b.zf);
      sg.setTransform(1, 0, 0, 1, 0, 0); sg.clearRect(0, 0, W, H); sg.setTransform(g.getTransform()); sg.lineCap = 'round';
      for (const s of list) {
        const { pf, q, x, y, zf, th } = s;
        const fade = smooth(0, .05, q) * (1 - smooth(.8, 1, q));
        if (fade <= .01) continue;
        const size = (40 + q * 210) * pf.rr;                      // puff radius grows as it rises
        const low = clamp(1 - s.h / 950, 0, 1);
        const lit = clamp(low * (.25 + .75 * (zf + 1) / 2) * I * (.35 + pf.hot * 1.3), 0, 1);
        const shade = .72 + .28 * (zf + 1) / 2;
        // soft body under the strokes so the puff reads as one billow
        const bodyC = mix([46, 40, 52], [176, 84, 40], lit * .85);
        const bg2 = g.createRadialGradient(x, y, 0, x, y, size);
        bg2.addColorStop(0, css(bodyC, .95 * fade)); bg2.addColorStop(.7, css(bodyC, .75 * fade)); bg2.addColorStop(1, css(bodyC, 0));
        sg.fillStyle = bg2; sg.fillRect(x - size, y - size, size * 2, size * 2);
        const wrap = th + Math.PI / 2;
        for (const pt of pf.parts) {
          const px = x + pt.ox * size * .85, py = y + pt.oy * size * .85;
          const hot = lit * (pt.s < .65 ? 1 : .35) * clamp(1 - (pt.oy + 1) * .3, 0, 1) * 1.15;
          const base = mix(pt.c, pt.s < .3 ? [244, 150, 70] : [214, 104, 46], clamp(hot, 0, 1));
          const col = [base[0] * shade, base[1] * shade, base[2] * shade];
          const ang = Math.atan2(Math.sin(wrap) * .3, Math.cos(wrap)) + pt.ang * .6 + Math.sin(t * .8 + pt.s * 6) * .15;
          const rr2 = rng(pt.seedk + ((t * 12) | 0));            // stroke texture shimmers slowly, like repainting
          smear(sg, px, py, ang, size * .24 * pt.len, size * .15, col, .85 * fade, rr2, (pt.s - .5) * .4);
        }
      }

      g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.filter = 'blur(1.4px)'; g.drawImage(sm, 0, 0); g.filter = 'none'; g.restore();

      // embers: ballistic streaks, additive
      g.globalCompositeOperation = 'lighter';
      for (const m of embers) {
        const a = (t + m.ph) % ELIFE, q = a / ELIFE;
        const vy = m.vy + 900 * a, x = CRATER[0] + m.x0 + m.vx * a, y = CRATER[1] + m.vy * a + 450 * a * a;
        const len = .035;
        g.strokeStyle = `rgba(255,${200 + m.c * 55 | 0},${120 + m.c * 80 | 0},${(1 - q) * .9 * I})`;
        g.lineWidth = 2.2 + m.c * 2;
        g.beginPath(); g.moveTo(x, y); g.lineTo(x - m.vx * len, y - vy * len); g.stroke();
      }

      // blasts: shockwave rings (sky + sea) and lava bombs on ballistic arcs
      blasts.forEach((b, bi) => {
        const a = t - b; if (a < 0 || a > 3) return;
        g.globalCompositeOperation = 'lighter';
        if (a < 1.0) {
          const R = 60 + a * 1250, al = Math.pow(1 - a, 2);
          g.save(); g.filter = 'blur(9px)';
          for (let k = 0; k < 28; k++) {                       // ring broken into uneven, soft arcs
            const a0 = k / 28 * Math.PI * 2, a1 = a0 + Math.PI * 2 / 28 * (.55 + vnoise(k, bi * 3, seed) * .5);
            const rr = R * (1 + (vnoise(k * .7, a * 4 + bi, seed + 2) - .5) * .18);
            g.strokeStyle = `rgba(255,200,150,${.3 * al * (.5 + vnoise(k, 9, seed))})`; g.lineWidth = 46 * al + 6;
            g.beginPath(); g.ellipse(CRATER[0], CRATER[1], rr, rr * .8, 0, a0, a1); g.stroke();
          }
          g.strokeStyle = `rgba(255,150,90,${.28 * al})`; g.lineWidth = 16 * al + 3;
          g.beginPath(); g.ellipse(CX, HORIZON + 8, R * 1.15, R * .07, 0, 0, Math.PI * 2); g.stroke();
          g.restore();
        }
        for (const m of bombs[bi]) {
          const x = CRATER[0] + m.vx * a, y = CRATER[1] + m.vy * a + 450 * a * a, vy = m.vy + 900 * a;
          if (y > HORIZON + 30) continue;
          const al = clamp(1 - a / 3, 0, 1);
          g.strokeStyle = `rgba(255,120,40,${.5 * al})`; g.lineWidth = m.rad * 1.2;
          g.beginPath(); g.moveTo(x, y); g.lineTo(x - m.vx * .06, y - vy * .06); g.stroke();
          g.fillStyle = `rgba(255,${210 + m.c * 40 | 0},140,${al})`; g.beginPath(); g.arc(x, y, m.rad * .6, 0, Math.PI * 2); g.fill();
        }
        g.globalCompositeOperation = 'source-over';
      });

      // lightning
      const [bi, br] = flashAmt(t);
      if (bi >= 0 && br > 0) {
        const B = bolts[bi];
        g.fillStyle = `rgba(170,150,255,${.10 * br})`; g.fillRect(-100, -100, W + 200, H + 200);
        g.shadowColor = 'rgba(190,160,255,1)'; g.shadowBlur = 36 * br;
        g.strokeStyle = `rgba(200,180,255,${.55 * br})`; g.lineWidth = 12; drawPath(B.pts); B.branches.forEach(drawPath);
        g.shadowBlur = 12 * br; g.strokeStyle = `rgba(255,255,255,${br})`; g.lineWidth = 4.5; drawPath(B.pts);
        g.lineWidth = 2.5; B.branches.forEach(drawPath);
        g.shadowBlur = 0;
      }
      g.globalCompositeOperation = 'source-over';
      waves.forEach((w, wi) => drawWave(t - w, wi));
      g.setTransform(1, 0, 0, 1, 0, 0);
      // blast flash (screen space)
      for (const b of blasts) { const a = t - b; if (a >= 0 && a < .9) { g.globalCompositeOperation = 'lighter'; g.fillStyle = `rgba(255,${200 + 40 * Math.exp(-a * 12) | 0},170,${.5 * Math.exp(-a * 11)})`; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over'; } }
      if (opt.post !== false) post(g, t, { scary, duration, ash });
    }

    return { render, flashes, shakeAt };
  }

  // ---------------------------------------------------------------- shared painting helpers
  // Paint a colour field once: blurred under-paint + 3 stroke passes along a flow field.
  function paintField(ctx, colorAt, angleAt, seed, passes = [[11, 34, 9, .55], [7, 22, 6, .7], [5, 14, 4, .8]]) {
    const r = rng(seed);
    const step = 12;
    for (let y = 0; y < H; y += step) for (let x = 0; x < W; x += step) { ctx.fillStyle = css(colorAt(x, y)); ctx.fillRect(x, y, step, step); }
    ctx.filter = 'blur(10px)'; ctx.drawImage(ctx.canvas, 0, 0); ctx.filter = 'none';
    ctx.lineCap = 'round';
    for (const [sp, len, wid, al] of passes) {
      for (let y = -10; y < H + 10; y += sp) for (let x = -10; x < W + 10; x += sp) {
        const px = x + (r() - .5) * sp * 1.4, py = y + (r() - .5) * sp * 1.4;
        stroke(ctx, px, py, angleAt(px, py) + (r() - .5) * .35, len * (.7 + r() * .6), wid, colorAt(px, py), al, r, (r() - .5) * .25);
      }
    }
  }
  const mkCanvas = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return c; };
  const easeIO = k => (k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2);
  function birdsDraw(g, t, list, col) {        // silhouetted birds flapping across the sky
    g.strokeStyle = col; g.lineCap = 'round';
    for (const b of list) {
      const x = ((b.x + b.v * t) % (W + 200) + W + 200) % (W + 200) - 100, y = b.y + Math.sin(t * .7 + b.ph) * 14;
      const f = Math.sin(t * b.f + b.ph) * .6, s = b.s;
      g.lineWidth = 2.2 + s * .08;
      g.beginPath(); g.moveTo(x - s, y - s * f * .8); g.quadraticCurveTo(x - s * .4, y - s * .35, x, y); g.quadraticCurveTo(x + s * .4, y - s * .35, x + s, y - s * f * .8); g.stroke();
    }
  }

  // ---------------------------------------------------------------- twilight: a red sky over a town, a fjord or a beach
  // opt: fg "town" | "fjord" | "beach", sky "ash" | "nacreous", sky_to (local s: crossfade to nacreous),
  // wagon [t0, t1] (town), wave (beach, local s: a tsunami wall rises on the horizon and the crowd runs)
  function twilight(canvas, opt = {}) {
    const seed = opt.seed ?? 5, g = canvas.getContext('2d');
    const duration = opt.duration ?? 10, zoom = opt.zoom ?? [1.0, 1.08];
    const fg = opt.fg ?? 'town', sky0 = opt.sky ?? 'ash', skyTo = opt.sky_to;
    const fjord = fg === 'fjord', beach = fg === 'beach', town = !fjord && !beach;
    const HOR = fjord ? 1050 : beach ? 1010 : 1240;
    const shoreY = x => 1290 + Math.sin(x * .004 + 1) * 22 + (fbm(x * .01, 3, seed) - .5) * 20;   // beach: waterline
    const isle = x => Math.max(0, 70 - Math.abs(x - 830) * .42);                                     // beach: Krakatau far on the horizon
    // ---- shapes
    const bld = [];
    if (town) {
      const r = rng(seed + 3); let x = -40;
      while (x < W + 40) { const w = 70 + r() * 120, h = 120 + r() * 210; bld.push({ x0: x, x1: x + w, top: HOR - h, roof: r() < .45 ? 'gable' : 'flat', ch: r() < .6 ? x + w * (.2 + r() * .6) : null }); x += w + (r() < .3 ? 8 : 0); }
    }
    const steeple = { x: 690, w: 64, top: 560, base: HOR - 330 };
    const inTown = (x, y) => {
      if (y > HOR) return true;
      if (Math.abs(x - steeple.x) < steeple.w / 2 && y > steeple.base) return true;                  // tower
      const sp = steeple.base - steeple.top; if (y > steeple.top && y <= steeple.base && Math.abs(x - steeple.x) < (steeple.w / 2) * (y - steeple.top) / sp) return true;   // spire
      for (const b of bld) {
        if (x < b.x0 || x >= b.x1) continue;
        let top = b.top;
        if (b.roof === 'gable') top = b.top - 46 * (1 - Math.abs((x - b.x0) / (b.x1 - b.x0) - .5) * 2);
        if (y > top) return true;
        if (b.ch && Math.abs(x - b.ch) < 9 && y > b.top - 70) return true;
      }
      return false;
    };
    const hillL = x => 860 + Math.pow(x / 640, 1.6) * 200 + (fbm(x * .006, 2, seed) - .5) * 40;       // left headland falls to the water
    const hillR = x => 990 - Math.max(0, x - 560) * .1 + (fbm(x * .008, 4, seed) - .5) * 26;        // low far shore
    const railY = x => 1370 - x * .31;                                                                   // the bridge rail, rising to the right
    const fjordLand = (x, y) => (x < 680 && y > hillL(x)) || (y > hillR(x) && y < HOR + 4 && x > 420);
    // ---- sky colour fields
    const NAC = ['#f0a7c6', '#a5dcc0', '#94b9ef', '#f3d58f', '#c9a3ea'].map(hex);
    function skyCol(x, y, mode) {
      const k = clamp(y / HOR, 0, 1);
      const sw = fbm(x * .0032, y * .0032, seed + 11);
      if (mode === 'nacreous') {
        let c = k < .5 ? mix(hex('#141a36'), hex('#3a3566'), k / .5) : mix(hex('#3a3566'), hex('#d98a5a'), (k - .5) / .5);
        const band = Math.sin(y * .022 + Math.sin(x * .005 + sw * 3) * 2.6 + sw * 4);
        const hue = (y * .004 + x * .0017 + sw * 2.2) % 1, ci = Math.floor(((hue + 1) % 1) * NAC.length);
        const amt = clamp(band * .5 + .5, 0, 1) * smooth(.12, .3, k) * (1 - smooth(.62, .85, k));
        return mix(c, mix(NAC[ci], NAC[(ci + 1) % NAC.length], (hue * NAC.length) % 1), amt * .75);
      }
      // ash: blood-red flowing bands
      let c = k < .3 ? mix(hex('#1c1026'), hex('#5c1626'), k / .3) : k < .62 ? mix(hex('#5c1626'), hex('#c2301c'), (k - .3) / .32) : mix(hex('#c2301c'), hex('#f29a3e'), (k - .62) / .38);
      const band = Math.sin(y * .018 + Math.sin(x * .0045 + sw * 3) * 2.2 + sw * 5);
      c = mix(c, band > 0 ? hex('#e3542c') : hex('#3c0e1e'), Math.abs(band) * .32 * smooth(.1, .4, k));
      return c;
    }
    function fgCol(x, y) {
      if (beach) {
        if (y <= HOR && y > HOR - isle(x)) return mix(hex('#1c0e14'), hex('#3a1a1a'), fbm(x * .02, y * .02, seed) * .5);
        if (y <= HOR) return null;
        const sy = shoreY(x);
        if (y < sy) {                                                                                     // sea mirrors the red sky
          const k = clamp((y - HOR) / (sy - HOR), 0, 1), m = skyCol(x, HOR - (y - HOR) * 2.2, sky0);
          return mix(mix(m, hex('#2a1620'), .35 + k * .25), hex('#120c16'), k * .35);
        }
        const k = clamp((y - sy) / (H - sy), 0, 1);                                                      // wet sand near the water, dark dry sand
        const wet = clamp(1 - (y - sy) / 90, 0, 1);
        return mix(mix(hex('#4a2a20'), hex('#160c0a'), Math.pow(k, .7)), skyCol(x, 900, sky0), wet * .35);
      }
      if (fjord) {
        if (y > railY(x) - 7 && y < railY(x) + 7) return hex('#120806');                                // rail
        if (y > railY(x)) { const pl = Math.sin((y - railY(x)) * .09 - x * .03) > .82 ? .5 : 0;          // dark planks
          return mix(mix(hex('#2a1810'), hex('#0e0806'), clamp((y - railY(x)) / 380, 0, 1)), hex('#050303'), pl); }
        if (fjordLand(x, y)) return mix(hex('#241a30'), hex('#3e2a3e'), fbm(x * .01, y * .01, seed) * .8); // dark blue-violet hills
        if (y > HOR) {                                                                                     // fjord water mirrors the sky
          const m = skyCol(x, HOR - (y - HOR) * 1.3, sky0), k = clamp((y - HOR) / 400, 0, 1);
          return mix(mix(m, hex('#1a2440'), .35 + k * .3), hex('#0c1020'), k * .5);
        }
        return null;
      }
      if (y > HOR) {                                                                                       // wet street reflects the sky
        const k = clamp((y - HOR) / (H - HOR), 0, 1), m = skyCol(x, HOR - (y - HOR) * .6, sky0);
        return mix(mix(hex('#1a0c10'), m, .28 * (1 - k)), hex('#08050a'), k * .7);
      }
      if (inTown(x, y)) return mix(hex('#140c14'), hex('#2a1418'), fbm(x * .02, y * .02, seed + 5) * .6);
      return null;
    }
    const skyAng = (x, y) => Math.sin(x * .005 + y * .011 + fbm(x * .003, y * .003, seed) * 4) * (fjord ? .75 : .35);
    const fgAng = (x, y) => beach ? (y > HOR ? (fbm(x * .01, y * .03, seed) - .5) * .25 : Math.PI / 2) : (fjord ? (y > railY(x) ? -.31 + Math.PI * 0 : (fjordLand(x, y) ? Math.PI / 2 + (fbm(x * .01, y * .01, seed) - .5) : (fbm(x * .01, y * .03, seed) - .5) * .3)) : (y > HOR ? (fbm(x * .01, y * .03, seed) - .5) * .3 : Math.PI / 2));
    const paintScene = mode => {
      const c = mkCanvas(), cg = c.getContext('2d');
      paintField(cg, (x, y) => fgCol(x, y) || skyCol(x, y, mode), (x, y) => (fgCol(x, y) ? fgAng(x, y) : skyAng(x, y)), seed * 7 + (mode === 'nacreous' ? 2 : 1));
      return c;
    };
    const bgA = paintScene(sky0), bgB = skyTo != null ? paintScene('nacreous') : null;
    // ---- animated pieces
    const r0 = rng(seed + 41);
    const swirls = Array.from({ length: 90 }, () => ({ x: r0() * W, y: 40 + r0() * (HOR - 260), v: 6 + r0() * 14, l: 60 + r0() * 140, w: 6 + r0() * 10, ph: r0() * 6, c: r0() }));
    const birds = Array.from({ length: 7 }, () => ({ x: r0() * W, y: 300 + r0() * 450, v: 22 + r0() * 30, f: 6 + r0() * 4, ph: r0() * 6, s: 14 + r0() * 14 }));
    const windows = [];
    for (const b of bld) for (let y = b.top + 30; y < HOR - 30; y += 44) for (let x = b.x0 + 18; x < b.x1 - 18; x += 34) if (r0() < .14) windows.push({ x: x + (r0() - .5) * 8, y, ph: r0() * 9 });
    const people = Array.from({ length: town ? 14 : 0 }, () => ({ x: 40 + r0() * 1000, s: .8 + r0() * .4, up: r0() < .5 }));
    const wagon = opt.wagon == null ? null : (Array.isArray(opt.wagon) ? opt.wagon : [opt.wagon, opt.wagon + 4.5]);   // fire wagon crossing
    function person(x, yb, s, up) {               // small silhouette, some pointing at the sky
      g.fillStyle = '#07040a'; g.strokeStyle = '#07040a'; g.lineCap = 'round';
      g.beginPath(); g.ellipse(x, yb - 74 * s, 9 * s, 10 * s, 0, 0, Math.PI * 2); g.fill();
      g.beginPath(); g.moveTo(x - 13 * s, yb - 62 * s); g.lineTo(x + 13 * s, yb - 62 * s); g.lineTo(x + 16 * s, yb - 4 * s); g.lineTo(x - 16 * s, yb - 4 * s); g.fill();
      if (up) { g.lineWidth = 6 * s; g.beginPath(); g.moveTo(x + 10 * s, yb - 58 * s); g.lineTo(x + 30 * s, yb - 100 * s); g.stroke(); }
    }
    function drawWagon(t) {
      const k = clamp((t - wagon[0]) / (wagon[1] - wagon[0]), 0, 1); if (k <= 0 || k >= 1) return;
      const x = lerp(-360, W + 360, k), yb = HOR + 150, bob = Math.sin(t * 14) * 3;
      g.fillStyle = '#060308'; g.strokeStyle = '#060308'; g.lineCap = 'round';
      for (let i = 0; i < 2; i++) {               // two horses
        const hx = x + 150 + i * 70, leg = Math.sin(t * 14 + i) * 16;
        g.beginPath(); g.ellipse(hx, yb - 70 + bob, 44, 22, 0, 0, Math.PI * 2); g.fill();
        g.beginPath(); g.ellipse(hx + 46, yb - 98 + bob, 14, 26, -.6, 0, Math.PI * 2); g.fill();
        g.lineWidth = 7; for (const d of [-26, 26]) { g.beginPath(); g.moveTo(hx + d, yb - 56); g.lineTo(hx + d + leg * (d > 0 ? 1 : -1), yb); g.stroke(); }
      }
      g.fillRect(x - 120, yb - 110 + bob, 210, 60);                     // body + ladder + boiler
      g.fillRect(x - 60, yb - 160 + bob, 60, 52);
      g.lineWidth = 5; g.beginPath(); g.moveTo(x - 140, yb - 124 + bob); g.lineTo(x + 100, yb - 124 + bob); g.stroke();
      for (const wx of [x - 80, x + 50]) { g.lineWidth = 6; g.beginPath(); g.arc(wx, yb - 30, 30, 0, Math.PI * 2); g.stroke(); }
      g.globalCompositeOperation = 'lighter';                          // swinging lantern
      const lx = x + 96, ly = yb - 132 + bob + Math.sin(t * 7) * 4;
      const gl = g.createRadialGradient(lx, ly, 0, lx, ly, 120); gl.addColorStop(0, 'rgba(255,210,120,.9)'); gl.addColorStop(.2, 'rgba(255,150,60,.35)'); gl.addColorStop(1, 'rgba(255,120,40,0)');
      g.fillStyle = gl; g.fillRect(lx - 120, ly - 120, 240, 240); g.globalCompositeOperation = 'source-over';
    }
    // ---- beach: the tsunami seen from the shore, a crowd running from it
    const WAVE = opt.wave, WD = 6.5;                       // seconds from the first sight of the wall to the shore
    const rb = rng(seed + 88);
    const runners = Array.from({ length: beach ? 34 : 0 }, (_, i) => {
      const depth = Math.pow(rb(), .7), y = 1360 + depth * 560, sc = (.75 + depth * 1.35) * 1.25;
      return { x: rb() * (W + 200) - 100, y, sc, dir: rb() < .5 ? -1 : 1, v: (55 + rb() * 70) * sc, react: rb() * 1.6, ph: rb() * 6, toward: rb() < .35, arm: rb() < .3 };
    });
    const palms = beach ? [{ x: 40, base: 1720, h: 900, lean: .2, s: 1.05 }, { x: 1050, base: 1660, h: 820, lean: -.26, s: .95 }, { x: 900, base: 1400, h: 470, lean: -.1, s: .6 }] : [];
    const waveK = t => (WAVE == null ? -1 : (t - WAVE) / WD);
    function runner(R, t) {
      const q = t - (WAVE ?? 0) - R.react;
      const s = R.sc, col = '#050205';
      let x = R.x, y = R.y, pose = 0, flip = R.dir;
      if (WAVE != null && q > 0) {                         // running: side-on, leaning forward, limbs swinging
        x = ((R.x + 150 + R.dir * R.v * q) % (W + 300) + W + 300) % (W + 300) - 150; if (R.toward) y = R.y + Math.min(q * 30 * s, 160);   // a steady stream fleeing across the beach
        pose = 1;
      }
      const ph = t * 11 + R.ph, sw = Math.sin(ph);
      g.strokeStyle = col; g.fillStyle = col; g.lineCap = 'round';
      const hip = [x, y - 46 * s], lean = pose ? .35 * flip : 0;
      const sh = [hip[0] + Math.sin(lean) * 44 * s, hip[1] - Math.cos(lean) * 44 * s];
      g.lineWidth = 19 * s; g.beginPath(); g.moveTo(hip[0], hip[1]); g.lineTo(sh[0], sh[1]); g.stroke();             // torso
      g.beginPath(); g.arc(sh[0] + Math.sin(lean) * 15 * s, sh[1] - 15 * s, 10.5 * s, 0, Math.PI * 2); g.fill();      // head
      g.lineWidth = 9.5 * s;
      if (pose) {
        for (const sg of [1, -1]) {                                                                                       // legs
          const a = sw * sg * .9;
          const kx = hip[0] + Math.sin(a) * 24 * s * flip, ky = hip[1] + Math.cos(a) * 22 * s;
          g.beginPath(); g.moveTo(hip[0], hip[1]); g.lineTo(kx, ky); g.lineTo(kx + Math.sin(a - .9 * sg) * 22 * s * flip, ky + 22 * s); g.stroke();
          const b = -sw * sg * 1.1;                                                                                       // arms (some thrown up in panic)
          if (R.arm && sg > 0) { g.beginPath(); g.moveTo(sh[0], sh[1]); g.lineTo(sh[0] - 6 * s * flip, sh[1] - 34 * s + sw * 4 * s); g.stroke(); }
          else { g.beginPath(); g.moveTo(sh[0], sh[1]); g.lineTo(sh[0] + Math.sin(b) * 26 * s * flip, sh[1] + Math.cos(b) * 20 * s); g.stroke(); }
        }
      } else {                                                                                                            // standing, looking at the sea
        for (const d of [-5, 5]) { g.beginPath(); g.moveTo(hip[0] + d * s, hip[1]); g.lineTo(hip[0] + d * 1.4 * s, y); g.stroke(); }
        for (const d of [-1, 1]) { g.beginPath(); g.moveTo(sh[0], sh[1] + 4 * s); g.lineTo(sh[0] + d * 10 * s, sh[1] + 40 * s); g.stroke(); }
      }
    }
    function drawPalm(P, t, gust) {
      const sway = Math.sin(t * 1.1 + P.x) * .03 + gust * .1 * Math.sin(t * 3.3 + P.x);
      const lean = P.lean + sway, topX = P.x + Math.sin(lean) * P.h, topY = P.base - Math.cos(lean) * P.h;
      const cx = P.x + (topX - P.x) * .15 + 60 * Math.sign(P.lean) * P.s, cy = (P.base + topY) / 2;
      g.fillStyle = '#060205'; g.strokeStyle = '#060205'; g.lineCap = 'round';
      // tapered trunk, bulging slightly at the base, with ring notches
      const N = 24, pts = [];
      for (let i = 0; i <= N; i++) { const u = i / N, a = (1 - u) * (1 - u), b = 2 * (1 - u) * u, c = u * u; pts.push([a * P.x + b * cx + c * topX, a * P.base + b * cy + c * topY, (34 - 20 * u + (u < .1 ? (.1 - u) * 90 : 0)) * P.s]); }
      g.beginPath();
      pts.forEach(([x, y, w], i) => { const [nx, ny] = i < N ? [pts[i + 1][0] - x, pts[i + 1][1] - y] : [x - pts[i - 1][0], y - pts[i - 1][1]], l = Math.hypot(nx, ny) || 1; (i ? g.lineTo.bind(g) : g.moveTo.bind(g))(x - ny / l * w / 2, y + nx / l * w / 2); });
      for (let i = N; i >= 0; i--) { const [x, y, w] = pts[i], [nx, ny] = i < N ? [pts[i + 1][0] - x, pts[i + 1][1] - y] : [x - pts[i - 1][0], y - pts[i - 1][1]], l = Math.hypot(nx, ny) || 1; g.lineTo(x + ny / l * w / 2, y - nx / l * w / 2); }
      g.closePath(); g.fill();
      // fronds: arch out and droop, leaflets hang off both sides
      const F = 9;
      for (let f = 0; f < F; f++) {
        const ang = -Math.PI + (f + .5) / F * Math.PI + (f % 2 ? .12 : -.08) + sway * 1.5 + Math.sin(t * 2.1 + f * 1.7) * .04 * (1 + gust * 3);
        const L = (230 + ((f * 37) % 3) * 45) * P.s, dx = Math.cos(ang), up = Math.max(-Math.sin(ang), .15);
        const c1 = [topX + dx * L * .45, topY - up * L * .45], e = [topX + dx * L, topY + L * (.35 - up * .25)];
        g.lineWidth = 7 * P.s; g.beginPath(); g.moveTo(topX, topY); g.quadraticCurveTo(c1[0], c1[1], e[0], e[1]); g.stroke();
        for (let k = 2; k <= 16; k++) {
          const u = k / 17, a = (1 - u) * (1 - u), b = 2 * (1 - u) * u, c = u * u;
          const px = a * topX + b * c1[0] + c * e[0], py = a * topY + b * c1[1] + c * e[1];
          const ll = L * .2 * (1 - u * .55);
          for (const side of [-1, 1]) {
            g.lineWidth = 5 * P.s * (1 - u * .4);
            g.beginPath(); g.moveTo(px, py); g.quadraticCurveTo(px + side * ll * .35 + dx * ll * .2, py + ll * .25, px + side * ll * .3 + dx * ll * .45, py + ll * .9); g.stroke();
          }
        }
      }
      g.beginPath(); g.arc(topX, topY + 6 * P.s, 16 * P.s, 0, Math.PI * 2); g.fill();          // crown + coconuts
    }
    function drawBeach(t) {
      // Krakatau far away: glow + a dark column leaning over the horizon
      g.globalCompositeOperation = 'lighter';
      const gl = g.createRadialGradient(830, HOR - 60, 0, 830, HOR - 60, 240);
      gl.addColorStop(0, `rgba(255,170,90,${.55 + .1 * Math.sin(t * 7)})`); gl.addColorStop(1, 'rgba(255,80,30,0)');
      g.fillStyle = gl; g.fillRect(590, HOR - 300, 480, 480); g.globalCompositeOperation = 'source-over';
      for (let i = 0; i < 26; i++) { const rr = rng(seed + 950 + i), h = ((t * 22 + rr() * 500) % 500); g.fillStyle = `rgba(30,18,24,${.5 * (1 - h / 520)})`; g.beginPath(); g.arc(830 + h * .25 + (rr() - .5) * 60, HOR - 70 - h, 26 + h * .18, 0, Math.PI * 2); g.fill(); }
      const k = waveK(t);
      // the wall: a dark line on the horizon that grows and rolls toward the beach
      if (k > -.01) {
        const q = clamp(k, 0, 1.15), e = Math.pow(clamp(q, 0, 1), 1.3);
        const base = lerp(HOR + 4, 1310, e), hgt = lerp(12, 640, Math.pow(clamp(q, 0, 1), 1.1));
        const crest = x => base - hgt * (1 + .1 * Math.sin(x * .007 + t * 1.8) + .06 * (vnoise(x * .005, t * .7, seed + 9) - .5));
        const grd = g.createLinearGradient(0, base - hgt * 1.1, 0, base);
        grd.addColorStop(0, 'rgba(70,40,48,.98)'); grd.addColorStop(.2, 'rgba(30,22,34,.99)'); grd.addColorStop(1, 'rgba(10,8,14,1)');
        g.fillStyle = grd; g.beginPath(); g.moveTo(-60, base + 30);
        for (let x = -60; x <= W + 60; x += 18) g.lineTo(x, crest(x));
        g.lineTo(W + 60, base + 30); g.closePath(); g.fill();
        const rr = rng(seed + 451);
        for (let i = 0; i < 140; i++) {                    // streaks on the face, lit red by the sky
          const x = rr() * (W + 120) - 60, top = crest(x), y = top + rr() * hgt * .85;
          stroke(g, x, y, Math.PI / 2 + (rr() - .5) * .3, 20 + rr() * 50, 5 + rr() * 5, mix([30, 22, 34], [170, 70, 50], (1 - (y - top) / (hgt + 1)) * .6), .35, rr);
        }
        for (let i = 0; i < 180; i++) {                    // foam curling along the crest + spray in the wind
          const f = rng(seed + 1200 + i), x = f() * (W + 120) - 60, y = crest(x) + f() * 16 - 6, sz = (8 + f() * 18) * (.4 + e * 1.2);
          g.strokeStyle = `rgba(${215 + f() * 30 | 0},${190 + f() * 30 | 0},${190 + f() * 30 | 0},.8)`; g.lineWidth = sz * .45;
          g.beginPath(); g.moveTo(x - sz, y); g.quadraticCurveTo(x, y - sz * .8, x + sz, y + sz * .2); g.stroke();
          g.fillStyle = 'rgba(220,200,205,.35)'; g.beginPath(); g.arc(x + (f() - .5) * 50, y - f() * 60 * e - 10, 2 + f() * 3, 0, Math.PI * 2); g.fill();
        }
        // the sea drains back first (a band of bare wet sand) before the wall arrives
        const drain = smooth(0, .25, q) * (1 - smooth(.85, 1, q));
        if (drain > 0) { g.fillStyle = `rgba(40,22,20,${.55 * drain})`; g.beginPath(); g.moveTo(-60, 1330); for (let x = -60; x <= W + 60; x += 30) g.lineTo(x, shoreY(x) - 70 * drain); g.lineTo(W + 60, 1330); g.fill(); }
      }
      const gust = clamp(k * 1.4, 0, 1);
      runners.slice().sort((a, b) => a.y - b.y).forEach(R => runner(R, t));
      palms.forEach(P => drawPalm(P, t, gust));
    }
    const beachShake = t => { const k = waveK(t); return k > .35 ? .45 * smooth(.35, 1, k) : 0; };

    function render(t) {
      const k = clamp(t / duration, 0, 1), z = lerp(zoom[0], zoom[1], easeIO(k));
      g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over';
      g.fillStyle = '#0b0a12'; g.fillRect(0, 0, W, H);
      const amp = beach ? beachShake(t) * 14 : 0, sx = (vnoise(t * 30, 2.1, seed) - .5) * 2 * amp, sy = (vnoise(t * 33, 5.3, seed) - .5) * 2 * amp;
      g.setTransform(z, 0, 0, z, 540 - 540 * z + sx, 1000 - 1000 * z + sy);
      g.drawImage(bgA, 0, 0);
      if (bgB) { const m = smooth(skyTo, skyTo + 2.2, t); if (m > 0) { g.globalAlpha = m; g.drawImage(bgB, 0, 0); g.globalAlpha = 1; } }
      const nac = bgB ? smooth(skyTo, skyTo + 2.2, t) : (sky0 === 'nacreous' ? 1 : 0);
      // living sky: translucent swirl strokes drifting along the bands
      g.globalCompositeOperation = 'lighter'; g.lineCap = 'round';
      for (const s of swirls) {
        const x = ((s.x + s.v * t) % (W + 300) + W + 300) % (W + 300) - 150, y = s.y + Math.sin(t * .4 + s.ph) * 20;
        const ang = skyAng(x, y) + Math.sin(t * .3 + s.ph) * .2, a = .08 + .06 * Math.sin(t * .9 + s.ph);
        const c = nac > .5 ? NAC[(s.c * NAC.length) | 0] : (s.c < .5 ? [230, 80, 40] : [250, 160, 70]);
        g.strokeStyle = css(c, a * (fjord && fjordLand(x, y) ? 0 : 1)); g.lineWidth = s.w;
        g.beginPath(); g.moveTo(x - Math.cos(ang) * s.l / 2, y - Math.sin(ang) * s.l / 2); g.quadraticCurveTo(x, y + 14 * Math.sin(s.ph), x + Math.cos(ang) * s.l / 2, y + Math.sin(ang) * s.l / 2); g.stroke();
      }
      // water / wet street shimmer
      for (let i = 0; i < 60; i++) {
        const rr = rng(seed + 600 + i), y0 = fjord ? HOR + 10 + rr() * 300 : beach ? HOR + 8 + rr() * 250 : HOR + 20 + rr() * 520;
        const x = rr() * W + Math.sin(t * (.8 + rr()) + i) * 16; if (fjord && (y0 > railY(x) || x < 640 && y0 < hillL(x) + 60 && false)) continue;
        g.strokeStyle = `rgba(255,${120 + rr() * 80 | 0},70,${(.08 + .1 * (.5 + .5 * Math.sin(t * 2.4 + i))) * (1 - nac * .5)})`; g.lineWidth = 3 + rr() * 3;
        g.beginPath(); g.moveTo(x - 30, y0); g.lineTo(x + 30, y0 + (rr() - .5) * 3); g.stroke();
      }
      // lit windows (town) flicker softly
      for (const w of windows) { const a = .55 + .3 * Math.sin(t * 2 + w.ph) * Math.sin(t * 3.1 + w.ph * 2); g.fillStyle = `rgba(255,190,100,${a})`; g.fillRect(w.x, w.y, 12, 18); }
      g.globalCompositeOperation = 'source-over';
      birdsDraw(g, t, birds, 'rgba(10,6,12,.9)');
      if (town) { for (const p of people) person(p.x, HOR + 90 + p.s * 30, p.s * 1.1, p.up); if (wagon) drawWagon(t); }
      if (beach) drawBeach(t);
      if (fjord) {
        // rail posts and the top rail, painted dark against the water
        g.strokeStyle = '#0a0504'; g.lineCap = 'butt';
        for (let x = -40; x < W + 60; x += 120) { const y = railY(x); g.lineWidth = 12; g.beginPath(); g.moveTo(x, y - 6); g.lineTo(x, y + 64); g.stroke(); }
        g.lineWidth = 13; g.beginPath(); g.moveTo(-40, railY(-40) - 4); g.lineTo(W + 60, railY(W + 60) - 4); g.stroke();
        g.lineWidth = 6; g.beginPath(); g.moveTo(-40, railY(-40) + 34); g.lineTo(W + 60, railY(W + 60) + 34); g.stroke();
        // a lone walker by the rail, seen from behind, coat moving in the wind
        const x = 380, yb = railY(x) + 70, sw = Math.sin(t * 1.3) * 4;
        g.fillStyle = '#080406'; g.lineCap = 'round';
        g.beginPath(); g.moveTo(x - 30, yb - 186); g.quadraticCurveTo(x - 52, yb - 170, x - 50, yb - 130);   // shoulders
        g.lineTo(x - 58 + sw, yb - 8); g.quadraticCurveTo(x, yb + 6, x + 56 + sw, yb - 10);              // coat hem
        g.lineTo(x + 50, yb - 130); g.quadraticCurveTo(x + 52, yb - 172, x + 30, yb - 186); g.closePath(); g.fill();
        g.fillRect(x - 24, yb - 10, 14, 36); g.fillRect(x + 8, yb - 10, 14, 36);                          // legs
        g.beginPath(); g.ellipse(x, yb - 206, 21, 24, 0, 0, Math.PI * 2); g.fill();                       // head
        g.beginPath(); g.ellipse(x, yb - 226, 40, 8, -.05, 0, Math.PI * 2); g.fill();                     // hat brim
        g.beginPath(); g.moveTo(x - 20, yb - 228); g.lineTo(x - 17, yb - 262); g.lineTo(x + 18, yb - 262); g.lineTo(x + 21, yb - 228); g.fill();
        // warm rim light from the sky on the shoulder
        g.strokeStyle = 'rgba(255,120,60,.35)'; g.lineWidth = 3; g.beginPath(); g.moveTo(x + 30, yb - 186); g.quadraticCurveTo(x + 52, yb - 172, x + 50, yb - 130); g.stroke();
      }
    }
    return { render, flashes: [], shakeAt: t => (beach ? beachShake(t) : 0) };
  }

  // ---------------------------------------------------------------- globe: a painted Earth in space
  // opt: lon [from, to] (centre longitude over the segment), lat (tilt), rings (local s: pressure wave
  // circles from Krakatau), veil (local s: ash haze spreading), mark [lat, lon] (default Krakatau)
  const CONTINENTS = [
    [[-168, 66], [-140, 70], [-95, 72], [-80, 64], [-60, 55], [-55, 47], [-70, 43], [-76, 35], [-81, 25], [-97, 26], [-97, 18], [-87, 15], [-80, 8], [-92, 15], [-106, 23], [-117, 32], [-124, 40], [-124, 48], [-135, 58], [-152, 60], [-166, 60]],
    [[-80, 9], [-75, 11], [-62, 10], [-50, 2], [-35, -6], [-39, -14], [-48, -26], [-58, -35], [-65, -42], [-70, -54], [-74, -45], [-71, -30], [-70, -18], [-77, -10], [-81, -4], [-78, 2]],
    [[-10, 36], [10, 37], [32, 31], [43, 12], [51, 11], [40, -3], [40, -15], [33, -26], [20, -35], [14, -25], [12, -6], [9, 4], [-8, 4], [-17, 14], [-17, 21]],
    [[-10, 36], [-9, 43], [-2, 48], [5, 52], [8, 58], [20, 70], [30, 71], [40, 66], [40, 46], [28, 41], [20, 38], [12, 44], [3, 43]],
    [[40, 66], [70, 73], [110, 77], [140, 72], [180, 68], [170, 60], [155, 58], [140, 52], [135, 43], [122, 40], [122, 30], [110, 20], [106, 10], [100, 14], [98, 8], [92, 21], [80, 14], [77, 8], [72, 20], [62, 25], [56, 27], [48, 30], [35, 32], [36, 37], [40, 46]],
    [[35, 30], [44, 13], [52, 16], [58, 22], [56, 26], [48, 29]],
    [[114, -22], [122, -18], [130, -12], [137, -12], [142, -11], [146, -18], [153, -26], [150, -37], [141, -38], [131, -31], [116, -34], [114, -27]],
    [[95, 5], [98, 4], [104, -2], [106, -6], [100, -3], [96, 2]], [[105, -6], [114, -7], [116, -8.5], [106, -7.5]],
    [[109, 1], [112, 3], [117, 7], [119, 1], [116, -4], [110, -3]], [[119, 1], [125, 1], [122, -5], [120, -5]], [[131, -1], [141, -3], [150, -10], [141, -9], [134, -4]],
    [[-52, 60], [-20, 70], [-25, 82], [-60, 82], [-72, 77]], [[130, 31], [135, 34], [141, 41], [142, 45], [138, 37], [132, 33]], [[-6, 50], [2, 52], [-3, 58], [-6, 56]], [[44, -25], [50, -15], [49, -12], [44, -17]],
  ];
  function inPoly(x, y, poly) { let ins = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const [xi, yi] = poly[i], [xj, yj] = poly[j]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi) ins = !ins; } return ins; }
  let EARTH = null;                               // painted equirectangular texture, shared by every globe
  function earthTexture() {
    if (EARTH) return EARTH;
    const TW = 1024, TH = 512, c = document.createElement('canvas'); c.width = TW; c.height = TH; const cg = c.getContext('2d');
    const MW = 256, MH = 128, mask = new Uint8Array(MW * MH);
    for (let j = 0; j < MH; j++) for (let i = 0; i < MW; i++) { const lon = i / MW * 360 - 180, lat = 90 - j / MH * 180; mask[j * MW + i] = CONTINENTS.some(p => inPoly(lon, lat, p)) ? 1 : 0; }
    const land = (u, v) => { const i = clamp((u * MW) | 0, 0, MW - 1), j = clamp((v * MH) | 0, 0, MH - 1); return mask[j * MW + i]; };
    const col = (x, y) => {
      const u = x / TW, v = y / TH, lat = 90 - v * 180, n = fbm(u * 14, v * 7, 21);
      if (Math.abs(lat) > 70) return mix(hex('#c9ccd6'), hex('#e6e8ee'), n);
      if (land(u + (n - .5) * .012, v + (n - .5) * .02)) return mix(mix(hex('#6b5a34'), hex('#3d5a34'), clamp(1 - Math.abs(lat) / 50, 0, 1) * .8), hex('#8a6a3a'), n * .5);
      return mix(hex('#0f2a44'), hex('#1d4a66'), n * .7);
    };
    const r = rng(77);
    for (let y = 0; y < TH; y += 8) for (let x = 0; x < TW; x += 8) { cg.fillStyle = css(col(x, y)); cg.fillRect(x, y, 8, 8); }
    cg.filter = 'blur(4px)'; cg.drawImage(c, 0, 0); cg.filter = 'none'; cg.lineCap = 'round';
    for (const [sp, len, wid, al] of [[6, 16, 5, .6], [4, 9, 3, .75]]) for (let y = 0; y < TH; y += sp) for (let x = 0; x < TW; x += sp) {
      const px = x + (r() - .5) * sp, py = y + (r() - .5) * sp;
      stroke(cg, px, py, (fbm(px * .01, py * .01, 5) - .5) * 1.2, len * (.7 + r() * .6), wid, col(px, py), al, r);
    }
    EARTH = cg.getImageData(0, 0, TW, TH); EARTH.TW = TW; EARTH.TH = TH;
    return EARTH;
  }
  function globe(canvas, opt = {}) {
    const seed = opt.seed ?? 3, g = canvas.getContext('2d');
    const duration = opt.duration ?? 10, zoom = opt.zoom ?? [1.0, 1.05];
    const lonR = opt.lon ?? [80, 120], lat0 = (opt.lat ?? 8) * Math.PI / 180;
    const CXg = 540, CYg = 860, R = opt.radius ?? 400;
    const mark = opt.mark ?? [-6.1, 105.4];
    const rings = opt.rings, veil = opt.veil;
    const tex = earthTexture();
    // space backdrop, painted once
    const bg = mkCanvas(), bgc = bg.getContext('2d');
    paintField(bgc, (x, y) => mix(hex('#06050c'), hex('#1a1030'), fbm(x * .003, y * .003, seed + 2) * .9 * clamp(1 - Math.hypot(x - CXg, y - CYg) / 1300, 0, 1)),
      (x, y) => fbm(x * .003, y * .003, seed) * 6, seed + 9, [[12, 30, 8, .5], [7, 18, 5, .6]]);
    const rs = rng(seed + 12);
    const stars = Array.from({ length: 260 }, () => ({ x: rs() * W, y: rs() * H, s: .6 + rs() * 2.2, ph: rs() * 6 }));
    // sphere rendered per pixel at half resolution into a small canvas
    const S = 2, SW = Math.ceil(2 * R / S), sc = document.createElement('canvas'); sc.width = SW; sc.height = SW;
    const scx = sc.getContext('2d'), img = scx.createImageData(SW, SW);
    const L = (() => { const v = [-.55, -.45, .7], n = Math.hypot(...v); return v.map(a => a / n); })();
    const toVec = (la, lo) => { la *= Math.PI / 180; lo *= Math.PI / 180; return [Math.cos(la) * Math.sin(lo), Math.sin(la), Math.cos(la) * Math.cos(lo)]; };
    const M = toVec(mark[0], mark[1]);
    function project(v, lonC) {                  // world unit vector -> screen (x, y, depth) for the current rotation
      const c = Math.cos(-lonC), s = Math.sin(-lonC);
      let x = v[0] * c + v[2] * s, z = -v[0] * s + v[2] * c, y = v[1];
      const ct = Math.cos(lat0), st = Math.sin(lat0);
      const y2 = y * ct - z * st, z2 = y * st + z * ct;
      return [CXg + x * R, CYg - y2 * R, z2];
    }
    function render(t) {
      const k = clamp(t / duration, 0, 1), z = lerp(zoom[0], zoom[1], easeIO(k));
      const lonC = lerp(lonR[0], lonR[1], easeIO(k)) * Math.PI / 180;
      g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over';
      g.fillStyle = '#05040a'; g.fillRect(0, 0, W, H);
      g.setTransform(z, 0, 0, z, 540 - 540 * z, CYg - CYg * z);
      g.drawImage(bg, 0, 0);
      for (const s of stars) { g.fillStyle = `rgba(230,220,255,${.35 + .35 * Math.sin(t * 2 + s.ph)})`; g.fillRect(s.x, s.y, s.s, s.s); }
      // ash veil radius (angular, radians) grows from the mark
      const vr = veil != null ? Math.pow(clamp((t - veil) / 3.5, 0, 1), .8) * 2.6 : -1;
      const ct = Math.cos(lat0), st = Math.sin(lat0), cl = Math.cos(lonC), sl = Math.sin(lonC);
      const d = img.data, TW = tex.TW, TH = tex.TH, td = tex.data;
      for (let j = 0; j < SW; j++) for (let i = 0; i < SW; i++) {
        const nx = (i * S + S / 2 - R) / R, ny = -(j * S + S / 2 - R) / R, q = 1 - nx * nx - ny * ny, o = (j * SW + i) * 4;
        if (q <= 0) { d[o + 3] = 0; continue; }
        const nz = Math.sqrt(q);
        // undo tilt, then rotation -> world vector
        const y = ny * ct + nz * st, zz = -ny * st + nz * ct;
        const wx = nx * cl + zz * sl, wz = -nx * sl + zz * cl;
        const la = Math.asin(clamp(y, -1, 1)), lo = Math.atan2(wx, wz);
        const u = ((lo / (2 * Math.PI) + .5) * TW) | 0, v = clamp(((.5 - la / Math.PI) * TH) | 0, 0, TH - 1), to = (v * TW + (u % TW)) * 4;
        let rr = td[to], gg = td[to + 1], bb = td[to + 2];
        if (vr > 0) {                            // ash haze: grey-red, thicker near the source, ragged edge
          const ang = Math.acos(clamp(wx * M[0] + y * M[1] + wz * M[2], -1, 1));
          const edge = vr * (1 - .35 * Math.abs(y)) + (fbm(lo * 3, la * 3, seed) - .5) * .5;
          const h = smooth(.15, -.25, ang - edge) * (.72 + .2 * fbm(lo * 6 + t * .2, la * 6, seed + 4));
          rr = lerp(rr, 168, h); gg = lerp(gg, 120, h); bb = lerp(bb, 110, h);
        }
        const lit = clamp(nx * L[0] + ny * -L[1] + nz * L[2], 0, 1), sh = .12 + .95 * Math.pow(lit, .8);
        const rim = Math.pow(1 - nz, 3);
        d[o] = clamp(rr * sh + rim * 60, 0, 255); d[o + 1] = clamp(gg * sh + rim * 90, 0, 255); d[o + 2] = clamp(bb * sh + rim * 150, 0, 255); d[o + 3] = 255;
      }
      scx.putImageData(img, 0, 0);
      // atmosphere glow behind + sphere
      g.globalCompositeOperation = 'lighter';
      const at = g.createRadialGradient(CXg, CYg, R * .95, CXg, CYg, R * 1.25);
      at.addColorStop(0, vr > 0 ? 'rgba(220,120,90,.35)' : 'rgba(110,160,255,.35)'); at.addColorStop(1, 'rgba(60,90,200,0)');
      g.fillStyle = at; g.beginPath(); g.arc(CXg, CYg, R * 1.25, 0, Math.PI * 2); g.fill();
      g.globalCompositeOperation = 'source-over';
      g.imageSmoothingEnabled = true; g.drawImage(sc, CXg - R, CYg - R, 2 * R, 2 * R);
      // pressure-wave rings: small circles at growing angular distance from Krakatau (out and back)
      if (rings != null) {
        const ax = Math.abs(M[1]) < .9 ? [0, 1, 0] : [1, 0, 0];
        const e1 = (() => { const c = [M[1] * ax[2] - M[2] * ax[1], M[2] * ax[0] - M[0] * ax[2], M[0] * ax[1] - M[1] * ax[0]], n = Math.hypot(...c); return c.map(a => a / n); })();
        const e2 = [M[1] * e1[2] - M[2] * e1[1], M[2] * e1[0] - M[0] * e1[2], M[0] * e1[1] - M[1] * e1[0]];
        g.save(); g.globalCompositeOperation = 'lighter'; g.lineCap = 'round';
        for (let n = 0; n < 4; n++) {
          const a = t - rings - n * .9; if (a < 0) continue;
          const ang = (a * 1.15) % Math.PI, fade = .9 - .15 * n;
          const pts = [];
          for (let s = 0; s <= 120; s++) { const ph = s / 120 * Math.PI * 2, c = Math.cos(ang), sn = Math.sin(ang); pts.push(project([M[0] * c + (e1[0] * Math.cos(ph) + e2[0] * Math.sin(ph)) * sn, M[1] * c + (e1[1] * Math.cos(ph) + e2[1] * Math.sin(ph)) * sn, M[2] * c + (e1[2] * Math.cos(ph) + e2[2] * Math.sin(ph)) * sn], lonC)); }
          for (const [lw, al, blur] of [[22, .22, 'blur(8px)'], [6, .75, 'none']]) {
            g.filter = blur; g.strokeStyle = `rgba(255,190,130,${al * fade})`; g.lineWidth = lw;
            g.beginPath(); let on = false;
            for (const p of pts) { if (p[2] > 0) { on ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]); on = true; } else on = false; }
            g.stroke();
          }
        }
        g.filter = 'none'; g.restore();
      }
      // Krakatau marker: a pulsing ember when on the visible side
      const pm = project(M, lonC);
      if (pm[2] > .05) {
        const pu = .5 + .5 * Math.sin(t * 5);
        g.globalCompositeOperation = 'lighter';
        const gm = g.createRadialGradient(pm[0], pm[1], 0, pm[0], pm[1], 70 + pu * 30); gm.addColorStop(0, `rgba(255,220,150,${.9 * pm[2]})`); gm.addColorStop(.25, `rgba(255,110,40,${.55 * pm[2]})`); gm.addColorStop(1, 'rgba(255,60,20,0)');
        g.fillStyle = gm; g.fillRect(pm[0] - 110, pm[1] - 110, 220, 220); g.globalCompositeOperation = 'source-over';
      }
    }
    return { render, flashes: [], shakeAt: () => 0 };
  }

  // ---------------------------------------------------------------- sequence: one painter per segment
  // opt.segments = [{start, end, cut, scene, ...painterOptions}] in global seconds (times inside a
  // segment's options are local to its start). Crossfades 0.6 s unless the segment is a `cut`.
  // flashes / blasts (global) go to the segments they fall in. One shared post pass on top.
  function sequence(canvas, opt = {}) {
    const g = canvas.getContext('2d'), FADE = opt.fade ?? .6, duration = opt.duration ?? 10;
    const flashes = opt.flashes ?? [], blasts = opt.blasts ?? [];
    const base = Object.assign({}, opt); delete base.segments; delete base.flashes; delete base.blasts;
    const segs = (opt.segments || []).map((s, i) => {
      const c = mkCanvas(), len = s.end - s.start;
      const inSeg = a => a.filter(x => x >= s.start - .05 && x < s.end).map(x => x - s.start);
      const o = Object.assign({}, base, s, { duration: len + FADE, flashes: inSeg(flashes), blasts: inSeg(blasts), post: false, seed: s.seed ?? (base.seed ?? 7) + i * 13 });
      const fn = API[s.scene]; if (!fn) throw new Error('paint.js: unknown scene ' + s.scene);
      return Object.assign({}, s, { c, p: fn(c, o), ash: s.ash ?? (s.scene === 'volcano') });
    });
    const active = t => { let i = 0; while (i < segs.length - 1 && t >= segs[i + 1].start) i++; return i; };
    function render(t) {
      const i = active(t), S = segs[i];
      S.p.render(t - S.start);
      g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; g.filter = 'none';
      let ashAmt = S.ash ? 1 : 0;
      const a = t - S.start;
      if (i > 0 && !S.cut && a < FADE) {
        const P = segs[i - 1]; P.p.render(t - P.start);
        const m = easeIO(a / FADE);
        g.drawImage(P.c, 0, 0); g.globalAlpha = m; g.drawImage(S.c, 0, 0); g.globalAlpha = 1;
        ashAmt = lerp(P.ash ? 1 : 0, ashAmt, m);
      } else g.drawImage(S.c, 0, 0);
      post(g, t, { scary: base.scary, duration, ashAmt });
      const end = duration - t;                   // last second sinks into the dark
      if (end < 1.4) { g.fillStyle = `rgba(4,2,6,${clamp(1 - end / 1.4, 0, 1) * .85})`; g.fillRect(0, 0, W, H); }
    }
    const shakeAt = t => { const S = segs[active(t)]; return S.p.shakeAt ? S.p.shakeAt(t - S.start) : 0; };
    return { render, flashes, shakeAt };
  }

  const API = { volcano, twilight, globe, sequence, post, stroke, fbm, rng };
  if (typeof window !== 'undefined') window.Paint = API;
})();
