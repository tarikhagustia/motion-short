// BEDAH: boots the project's model.js (BEDAH.film(fn)) on the Three.js stage and drives, every frame,
// the 3D picture, the pinned callouts, highlight glows, info cards and the header readout
// (big number + sparkline + status badge). Pure function of t.
(function () {
  const B = window.BEDAH;
  if (!B || !B.createStage) { console.error('bedah: stage library missing'); return; }
  const tl = DATA.timeline;
  const normW = w => (w || '').toLowerCase().replace(/[^\p{L}\p{N}±%]/gu, '');
  const sceneIdx = sid => DATA.scenes.findIndex(s => s.id === sid);
  const S = { B, THREE, DATA, missing: [] };

  // --- word clock: S.at("s03", "magnet", 0.05) = seconds into the video when that word starts
  S.at = function (sid, word, off = 0) {
    const si = sceneIdx(sid), want = normW(word);
    const w = tl.words.find(x => x.scene === si && normW(x.text).startsWith(want));
    if (!w) { S.missing.push(`${sid}:${word}`); return (tl.scenes[si] || tl.scenes[0]).start + off; }
    return w.start + off;
  };
  S.end = (sid, word) => { if (word === undefined) { const s = tl.scenes[sceneIdx(sid)]; return s ? s.end : tl.duration; }
    const si = sceneIdx(sid), want = normW(word); const w = tl.words.find(x => x.scene === si && normW(x.text).startsWith(want)); return w ? w.end : S.at(sid, word); };
  S.start = sid => (tl.scenes[sceneIdx(sid)] || { start: 0 }).start;
  S.duration = tl.duration;
  S.kf = B.kf; S.smooth = B.smooth; S.clamp01 = B.clamp01;
  // 0 -> 1 ramp between a and a + d (smoothstep)
  S.ramp = (t, a, d = 0.6) => B.smooth(B.clamp01((t - a) / d));
  // pulse that is 1 between a and b with soft edges
  S.on = (t, a, b, e = 0.25) => S.ramp(t, a, e) * (1 - S.ramp(t, b, e));

  S.stage = B.createStage(Object.assign({}, (window.BEDAH_OPTS || {})));
  const { stage } = S;

  // --- pinned callouts: S.label("MAGNET", obj, [x,y,z], {from, to, side: "left"|"right"})
  const labelHost = document.getElementById('bd-labels');
  const labels = [];
  S.label = function (text, obj, pos, o = {}) {
    const el = document.createElement('div');
    const side = o.side || 'left';
    el.className = 'bd-lbl ' + side + (o.dark === false ? ' light' : '');
    el.innerHTML = `<span>${side === 'left' ? text + ' →' : '← ' + text}</span>`;
    labelHost.appendChild(el);
    labels.push({ el, obj, pos, from: o.from ?? 0, to: o.to ?? 1e9, side });
    return el;
  };
  // --- highlight: the part being talked about turns yellow. S.glow(obj, from, to) or S.glow(obj, keys)
  const glows = [];
  S.glow = function (obj, a, b, color) {
    const target = new THREE.Color(color ?? B.HL);
    const mats = [];
    obj.traverse(m => { if (m.isMesh && !m.userData.hull) { m.material = stage.cloneMat(m.material); mats.push([m.material, m.material.color.clone()]); } });
    glows.push({ mats, target, k: Array.isArray(a) ? (t => B.kf(t, a)) : (t => S.on(t, a, b ?? 1e9)) });
  };
  // --- info card (HTML) floating over the picture: S.card(html, {from, to, x, y, w})
  const cards = [];
  S.card = function (html, o = {}) {
    const el = document.createElement('div');
    el.className = 'bd-card' + (o.class ? ' ' + o.class : '');
    el.innerHTML = html;
    el.style.left = (o.x ?? 80) + 'px'; el.style.top = (o.y ?? 560) + 'px'; el.style.width = (o.w ?? 920) + 'px';
    labelHost.appendChild(el);
    cards.push({ el, from: o.from ?? 0, to: o.to ?? 1e9 });
    return el;
  };

  const film = (B._film || (() => ({})))(S) || {};
  if (S.missing.length) console.error('bedah: words not found: ' + S.missing.join(', '));

  // --- header readout
  const valEl = document.getElementById('bd-val'), unitEl = document.getElementById('bd-unit');
  const badgeEl = document.getElementById('bd-badge'), spark = document.getElementById('bd-spark');
  const head = document.getElementById('bd-head');
  const fmt = (v, dec) => { const [i, f] = Math.abs(v).toFixed(dec).split('.');
    return (v < 0 ? '−' : '') + i.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (f ? ',' + f : ''); };
  const sp = film.spark;
  if (!film.readout) head.style.display = 'none';
  if (sp && spark) {
    const lines = (sp.lines || []).map(v => `<line class="thr" x1="0" x2="250" /><text class="thr-t" x="256">${fmt(v, 0)}</text>`).join('');
    spark.innerHTML = lines + '<path class="tr" d=""/><circle class="dot" r="5"/>';
  } else if (spark) spark.style.display = 'none';
  const sy = v => 54 - B.clamp01((v - sp.min) / (sp.max - sp.min)) * 48;

  STYLE.frame = function (t, si) {
    if (film.frame) film.frame(t, si);
    glows.forEach(g => { const k = B.clamp01(g.k(t)); g.mats.forEach(([m, base]) => m.color.copy(base).lerp(g.target, k)); });
    stage.scene.updateMatrixWorld();
    labels.forEach(L => {
      const k = B.clamp01((t - L.from) / 0.3) * (1 - B.clamp01((t - L.to) / 0.2));
      if (k <= 0) { L.el.style.opacity = 0; return; }
      const [x, y] = stage.toScreen(L.obj, L.pos);
      const w = L.el.offsetWidth, h = L.el.offsetHeight;
      L.el.style.left = Math.round(L.side === 'left' ? x - w - 8 : x + 8) + 'px';
      L.el.style.top = Math.round(y - h / 2) + 'px';
      const pop = k < 1 ? 0.6 + 0.4 * B.smooth(k) + Math.sin(k * Math.PI) * 0.12 : 1;
      L.el.style.opacity = k; L.el.style.transform = `scale(${pop.toFixed(3)})`;
    });
    cards.forEach(c => { const k = B.clamp01((t - c.from) / 0.35) * (1 - B.clamp01((t - c.to) / 0.25));
      c.el.style.opacity = k; c.el.style.transform = `translateY(${((1 - B.smooth(k)) * 30).toFixed(1)}px)`; });
    if (film.readout) {
      const r = film.readout(t);
      valEl.textContent = fmt(r.value, r.decimals ?? 0);
      unitEl.textContent = r.unit ?? '';
      head.classList.toggle('hot', !!r.hot);
      if (sp) {
        const n = 48, win = sp.window || 6; let d = '';
        for (let i = 0; i <= n; i++) { const tt = Math.max(0, t - win + win * i / n); const v = film.readout(tt).value;
          d += (i ? 'L' : 'M') + (i * 250 / n).toFixed(1) + ' ' + sy(v).toFixed(1); }
        spark.querySelector('.tr').setAttribute('d', d);
        const dot = spark.querySelector('.dot'); dot.setAttribute('cx', 250); dot.setAttribute('cy', sy(r.value));
        spark.querySelectorAll('.thr').forEach((l, i) => { const y = sy(sp.lines[i]); l.setAttribute('y1', y); l.setAttribute('y2', y); });
        spark.querySelectorAll('.thr-t').forEach((l, i) => l.setAttribute('y', sy(sp.lines[i]) + 6));
      }
    }
    const base = DATA.chrome || {}, sc = (DATA.scenes[si] || {}).chrome || {};
    badgeEl.className = 'bd-badge ' + (sc.badge_kind ?? base.badge_kind ?? 'note');
    stage.render();
  };
})();
