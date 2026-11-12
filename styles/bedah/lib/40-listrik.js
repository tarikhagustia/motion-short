// BEDAH.listrik: reusable household electrical equipment, modelled from reference photos
// (projects/listrik-rumah-aman/refs/SPEK.md). Units: metres. Brand-free labels.
// Each builder returns a THREE.Group; the origin is the mounting point noted per item, front = +z
// (rotate the group to face another way). Faces use canvas textures drawn once.
(function () {
  const B = window.BEDAH;

  function make(S) {
    const { stage, THREE } = S, { add } = stage;
    const T = (hex, ex) => stage.toon(hex, false, ex);
    const tex = (w, h, draw) => { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
      const t = new THREE.CanvasTexture(c); t.anisotropy = 4; return t; };
    const face = (w, h, map, parent, pos, extra = {}) => {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), T(0xffffff, Object.assign({ map }, extra)));
      if (pos) m.position.set(...pos); m.receiveShadow = true; parent.add(m); return m;
    };
    const rb = (w, h, d, r, bev = 0.002) => B.rbox(w, h, d, r, 1, bev);
    const glass = (op = 0.18, col = 0xffffff) => T(col, { transparent: true, opacity: op, depthWrite: false, roughness: 0.15 });
    const font = (px, w = 700) => `${w} ${px}px "Inter", Arial, sans-serif`;
    const rrect = (g, x, y, w, h, r) => { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); };

    // ------------------------------------------------------------ kWh meter prabayar (origin: back centre)
    function kwhMeter() {
      const g = new THREE.Group();
      const W = 0.16, H = 0.26, D = 0.075;
      add(rb(W, H, 0.02, 0.008), T(0xb9bcbf), g, [0, 0, 0.01]);                       // base
      add(rb(W - 0.008, 0.15, 0.05, 0.01), T(0xdfe2e3), g, [0, 0.05, 0.035]);          // upper housing
      const faceTex = tex(320, 300, (c, w, h) => {
        c.fillStyle = '#dfe2e3'; c.fillRect(0, 0, w, h);
        c.fillStyle = '#c8322b'; c.font = font(13); c.textAlign = 'center'; c.fillText('MERUSAK SEGEL DAN METER DIDENDA DAN DIPIDANA', w / 2, 20);
        c.fillStyle = '#9fae94'; rrect(c, 70, 34, 120, 42, 4); c.fill(); c.strokeStyle = '#6f7a69'; c.lineWidth = 2; c.stroke();
        c.fillStyle = '#f3c843'; c.fillRect(14, 36, 34, 34); c.fillStyle = '#c8322b'; c.beginPath(); c.moveTo(34, 40); c.lineTo(24, 56); c.lineTo(32, 56); c.lineTo(26, 68); c.lineTo(40, 50); c.lineTo(32, 50); c.closePath(); c.fill();
        c.fillStyle = '#333'; c.font = font(9, 600); c.fillText('MILIK PLN', 31, 82);
        c.font = font(11, 600); c.textAlign = 'left';
        ['Status Kredit', 'Tamper', 'imp/kWh'].forEach((s, i) => c.fillText(s, 72 + i * 52, 116));
        c.font = font(10, 500); c.fillText('Hijau : Cukup', 76, 132); c.fillText('Merah berkedip : Sedikit', 76, 146);
        c.font = font(20, 800); c.fillStyle = '#2a5ea8'; c.fillText('kWh', 12, 180); c.fillStyle = '#333';
        c.font = font(11, 600); ['METER PRABAYAR', 'Fase Tunggal 2 Kawat', '230V 5(60)A 50Hz', 'Kelas 1.0  IP54', 'No. Meter 1234 5678 901'].forEach((s, i) => c.fillText(s, 12, 200 + i * 16));
        c.fillStyle = '#c9cccd'; c.fillRect(12, 278, 110, 14);
      });
      face(W - 0.012, 0.145, faceTex, g, [0, 0.05, 0.0605]);
      // LCD display (its own texture so the reading can change)
      const lcdC = document.createElement('canvas'); lcdC.width = 160; lcdC.height = 56; const lcdT = new THREE.CanvasTexture(lcdC);
      const lcd = face(0.058, 0.02, lcdT, g, [-0.0085, 0.1, 0.0612]);
      let lastTxt = null;
      g.userData.setDisplay = txt => { if (txt === lastTxt) return; lastTxt = txt; const c = lcdC.getContext('2d');
        c.fillStyle = '#a9b99e'; c.fillRect(0, 0, 160, 56); c.fillStyle = '#1f2a1c'; c.font = font(40, 700); c.textAlign = 'right'; c.fillText(txt, 152, 46); lcdT.needsUpdate = true; };
      g.userData.setDisplay('21.84');
      // optical port (round, top right) + LEDs
      add(new THREE.TorusGeometry(0.018, 0.003, 10, 28), T(0xcfd2d3), g, [0.05, 0.098, 0.062]);
      add(new THREE.CircleGeometry(0.016, 24), T(0xe9ebec), g, [0.05, 0.098, 0.0612]);
      const leds = [0x37c45a, 0x7a7d80, 0x7a7d80].map((c, i) => add(new THREE.SphereGeometry(0.0035, 10, 8), new THREE.MeshBasicMaterial({ color: c }), g, [-0.034 + i * 0.026, 0.074, 0.062]));
      g.userData.leds = leds;
      // keypad: dark rounded bezel + 12 raised keys (enter green)
      add(rb(0.075, 0.072, 0.008, 0.012), T(0x2c2e31), g, [0.03, 0.015, 0.062]);
      const keyTex = (lbl, green) => tex(64, 52, (c, w, h) => { c.fillStyle = green ? '#3fb34f' : '#55585c'; rrect(c, 0, 0, w, h, 10); c.fill();
        c.fillStyle = '#fff'; c.font = font(30, 700); c.textAlign = 'center'; c.fillText(lbl, w / 2, 38); });
      ['1', '2', '3', '4', '5', '6', '7', '8', '9', '←', '0', '↵'].forEach((k, i) => {
        const key = add(rb(0.016, 0.012, 0.005, 0.003), T(i === 11 ? 0x3fb34f : 0x55585c), g, [0.006 + (i % 3) * 0.021, 0.036 - Math.floor(i / 3) * 0.0155, 0.0675]);
        face(0.0155, 0.0115, keyTex(k, i === 11), key, [0, 0, 0.0026]);
      });
      // terminal block + MCB PLN with red seal sticker (lower section)
      add(rb(0.13, 0.03, 0.03, 0.004), T(0xf2f2ee), g, [0, -0.045, 0.03]);
      for (let i = 0; i < 5; i++) for (let j = 0; j < 2; j++) add(new THREE.CylinderGeometry(0.004, 0.004, 0.004, 12), T(0x8d9093), g, [-0.05 + i * 0.025, -0.04 - j * 0.011, 0.046], [Math.PI / 2, 0, 0]);
      const mcbPln = add(rb(0.036, 0.05, 0.04, 0.004), T(0xf4f4f0), g, [0, -0.095, 0.03]);
      face(0.03, 0.02, tex(96, 64, (c) => { c.fillStyle = '#f4f4f0'; c.fillRect(0, 0, 96, 64); c.fillStyle = '#d33a31'; c.fillRect(6, 8, 40, 48); c.fillRect(54, 10, 36, 44);
        c.fillStyle = '#fff'; c.font = font(12, 800); c.fillText('SEGEL', 8, 36); c.fillStyle = '#1e5e3a'; c.fillRect(40, 22, 16, 22); }), mcbPln, [0, 0, 0.0205]);
      // transparent cover over everything
      add(rb(W, H, D, 0.01), glass(0.16), g, [0, 0, D / 2 + 0.002]);
      return g;
    }

    // ------------------------------------------------------------ DIN modules (origin: rail centre)
    function moduleLabel(txt, sub) {
      return tex(64, 72, (c, w, h) => { c.fillStyle = '#f4f4f0'; c.fillRect(0, 0, w, h); c.fillStyle = '#1d1f22'; c.font = font(26, 800); c.textAlign = 'center';
        c.fillText(txt, w / 2, sub ? 32 : 46); if (sub) { c.font = font(13, 700); c.fillStyle = '#555'; c.fillText(sub, w / 2, 58); } });
    }
    function mcb(o = {}) {          // 1 module, 18 mm. o.toggle colour, o.label "C10"
      const g = new THREE.Group(), W = 0.0175;
      add(rb(W, 0.085, 0.045, 0.002), T(0xf4f4f0), g, [0, 0, 0.0225]);
      add(rb(W, 0.045, 0.02, 0.002), T(0xf4f4f0), g, [0, 0, 0.055]);
      face(W - 0.003, 0.0165, moduleLabel(o.label || 'C10', o.sub), g, [0, -0.0128, 0.0652]);   // printed on the front step, under the lever
      [0.034, -0.034].forEach(y => add(new THREE.CylinderGeometry(0.0035, 0.0035, 0.002, 10), T(0x9a9da0), g, [0, y, 0.0455], [Math.PI / 2, 0, 0]));
      const lever = new THREE.Group(); lever.position.set(0, 0.006, 0.065); g.add(lever);
      add(rb(0.008, 0.016, 0.012, 0.002), T(o.toggle ?? 0x2b2d31), lever, [0, 0.006, 0.004]);
      g.userData.lever = lever;   // rotation.x: 0 = ON (up), ~1.0 = OFF (down)
      return g;
    }
    function rccb() {               // 2 modules, 36 mm, TEST button
      const g = new THREE.Group(), W = 0.0355;
      add(rb(W, 0.085, 0.045, 0.002), T(0xf4f4f0), g, [0, 0, 0.0225]);
      add(rb(W, 0.045, 0.02, 0.002), T(0xf4f4f0), g, [0, 0, 0.055]);
      face(W - 0.003, 0.0165, tex(128, 64, (c, w, h) => { c.fillStyle = '#f4f4f0'; c.fillRect(0, 0, w, h); c.fillStyle = '#1d1f22'; c.textAlign = 'center';
        c.font = font(22, 800); c.fillText('RCCB', w / 2, 24); c.font = font(14, 700); c.fillText('IΔn 30mA · 2P 40A', w / 2, 48); }), g, [0, -0.032, 0.0452]);
      const btn = add(new THREE.CylinderGeometry(0.0045, 0.0045, 0.004, 16), T(0xf3c843), g, [0.009, 0.03, 0.047], [Math.PI / 2, 0, 0]);
      face(0.006, 0.006, tex(32, 32, c => { c.fillStyle = '#f3c843'; c.fillRect(0, 0, 32, 32); c.fillStyle = '#222'; c.font = font(24, 800); c.textAlign = 'center'; c.fillText('T', 16, 25); }), btn, [0, 0.0021, 0], {}).rotation.x = -Math.PI / 2;
      const lever = new THREE.Group(); lever.position.set(-0.004, 0.006, 0.065); g.add(lever);
      add(rb(0.02, 0.016, 0.012, 0.002), T(0x2f6fbf), lever, [0, 0.006, 0.004]);
      g.userData.lever = lever; g.userData.test = btn;
      return g;
    }
    // box MCB: o.modules = [{type:'rccb'}|{type:'mcb', label, toggle}], origin = back centre on the wall
    function boxMcb(o = {}) {
      const g = new THREE.Group();
      const modW = (o.modules || []).reduce((a, m) => a + (m.type === 'rccb' ? 0.037 : 0.019), 0);
      const W = o.w ?? Math.max(0.16, modW + 0.06), H = 0.24, D = 0.085;
      add(rb(W, H, 0.012, 0.012), T(0xe7e7e2), g, [0, 0, 0.006]);
      [[0, H / 2 - 0.01, W, 0.02], [0, -H / 2 + 0.01, W, 0.02], [-W / 2 + 0.01, 0, 0.02, H], [W / 2 - 0.01, 0, 0.02, H]]
        .forEach(([x, y, w, h]) => add(rb(w, h, D, 0.006), T(0xdadad4), g, [x, y, D / 2]));
      add(B.box(W - 0.04, 0.035, 0.008), T(0xa7abaf), g, [0, 0, 0.016]);                // DIN rail
      add(rb(W - 0.04, 0.025, 0.006, 0.003), T(0x6f7377), g, [0, 0.075, 0.016]);          // label strip
      const mods = [];
      let x = -modW / 2;
      (o.modules || []).forEach(m => {
        const piece = m.type === 'rccb' ? rccb() : mcb(m);
        const w = m.type === 'rccb' ? 0.036 : 0.018;
        piece.position.set(x + w / 2, 0, 0.02); g.add(piece); mods.push(piece); x += w + 0.001;
      });
      const cover = add(rb(W - 0.01, H - 0.01, 0.006, 0.01), glass(0.12, 0x3a4048), g, [0, 0, D + 0.004]);
      g.userData.modules = mods; g.userData.cover = cover;
      return g;
    }

    // ------------------------------------------------------------ outside: pole, earth rod, splitzen
    function pole(o = {}) {         // origin: foot of the pole
      const g = new THREE.Group(), H = o.h ?? 9;
      add(new THREE.CylinderGeometry(0.1, 0.15, H, 16), T(0xa9aaa6), g, [0, H / 2, 0]);
      add(B.box(1.4, 0.08, 0.08), T(0x6e7276), g, [0, H - 0.5, 0]);
      [-0.55, -0.2, 0.2, 0.55].forEach(dx => add(new THREE.CylinderGeometry(0.03, 0.04, 0.12, 12), T(0xe9e4da), g, [dx, H - 0.4, 0]));
      add(B.box(0.12, 0.6, 0.12), T(0x3a3d42), g, [0.12, H - 1.4, 0]);                // cable clamp/box
      g.userData.top = [0.55, H - 0.35, 0];
      return g;
    }
    function earthRod(o = {}) {     // origin: ground level at the rod; rod goes down o.len
      const g = new THREE.Group(), L = o.len ?? 1.8;
      add(B.cyl(0.008, L, 12), T(0xc06a3a), g, [0, -L / 2, 0]);
      add(new THREE.ConeGeometry(0.008, 0.05, 12), T(0xc06a3a), g, [0, -L - 0.025, 0], [Math.PI, 0, 0]);
      add(rb(0.03, 0.03, 0.03, 0.004), T(0xc9a227), g, [0, -0.08, 0]);                  // brass clamp
      // bak kontrol: small concrete pit with a lid
      add(B.box(0.32, 0.25, 0.04), T(0xb8b4ab), g, [0, -0.1, 0.14]); add(B.box(0.32, 0.25, 0.04), T(0xb8b4ab), g, [0, -0.1, -0.14]);
      add(B.box(0.04, 0.25, 0.32), T(0xb8b4ab), g, [0.14, -0.1, 0]); add(B.box(0.04, 0.25, 0.32), T(0xb8b4ab), g, [-0.14, -0.1, 0]);
      g.userData.clamp = [0, -0.08, 0];
      return g;
    }
    function splitzen() {           // origin: base on the ridge
      const g = new THREE.Group();
      add(B.cyl(0.03, 0.18, 12), T(0x8e9296), g, [0, 0.09, 0]);
      add(B.cyl(0.009, 0.7, 12), T(0xc9cdd1, { metalness: 0.4, roughness: 0.35 }), g, [0, 0.53, 0]);
      add(new THREE.ConeGeometry(0.012, 0.1, 12), T(0xc9cdd1, { metalness: 0.4, roughness: 0.35 }), g, [0, 0.93, 0]);
      g.userData.top = [0, 0.98, 0];
      return g;
    }

    // ------------------------------------------------------------ appliances (origin: back centre / floor)
    function acSplit() {            // indoor unit, origin = back centre on the wall
      const g = new THREE.Group();
      add(rb(0.8, 0.28, 0.2, 0.06, 0.012), T(0xf6f6f2), g, [0, 0, 0.1]);
      add(rb(0.78, 0.17, 0.012, 0.03), T(0xfbfbf8), g, [0, 0.04, 0.2]);               // front panel
      for (let i = 0; i < 18; i++) add(B.box(0.012, 0.004, 0.13), T(0xd5d7d8), g, [-0.3 + i * 0.0355, 0.141, 0.1]);   // top intake grille
      add(B.box(0.66, 0.035, 0.03), T(0x4a4d52), g, [0, -0.11, 0.17]);                 // air outlet
      const louver = add(rb(0.66, 0.03, 0.01, 0.006), T(0xeeeeea), g, [0, -0.115, 0.192]);
      add(new THREE.SphereGeometry(0.005, 10, 8), new THREE.MeshBasicMaterial({ color: 0x4fd36b }), g, [0.3, -0.06, 0.206]);
      g.userData.louver = louver;
      return g;
    }
    function fridge() {             // 2-door, origin = floor centre
      const g = new THREE.Group(), W = 0.6, H = 1.5, D = 0.62;
      add(rb(W, H, D, 0.04, 0.01), T(0xeef1f2), g, [0, H / 2 + 0.03, 0]);
      add(B.box(W - 0.02, 0.012, 0.012), T(0x9aa1a7), g, [0, H * 0.68, D / 2 + 0.002]);   // freezer split
      [[H * 0.84, 0.22], [H * 0.42, 0.42]].forEach(([y, h]) => add(rb(0.02, h, 0.03, 0.008), T(0xc4c9cd), g, [-W / 2 + 0.05, y, D / 2 + 0.012]));
      [-0.22, 0.22].forEach(x => add(B.box(0.06, 0.03, 0.06), T(0x55595e), g, [x, 0.015, 0.2]));
      return g;
    }
    function riceCooker() {         // magic com, origin = bottom centre
      const g = new THREE.Group();
      add(B.lathe([[0, 0], [0.13, 0], [0.155, 0.03], [0.16, 0.16], [0.15, 0.2], [0, 0.2]], 48), T(0xf7f5ef), g);
      const lid = new THREE.Group(); lid.position.y = 0.2; g.add(lid);
      add(B.lathe([[0, 0], [0.152, 0], [0.13, 0.06], [0.06, 0.09], [0, 0.095]], 48), T(0xd9dcdf, { metalness: 0.2 }), lid);
      add(rb(0.07, 0.025, 0.03, 0.01), T(0x6a6e73), lid, [0, 0.1, 0]);
      add(rb(0.07, 0.07, 0.03, 0.01), T(0xe4e6e8), g, [0, 0.1, 0.155]);                 // switch panel
      const cookLed = add(new THREE.SphereGeometry(0.006, 10, 8), new THREE.MeshBasicMaterial({ color: 0xff8a2a }), g, [-0.015, 0.12, 0.172]);
      add(rb(0.02, 0.03, 0.012, 0.004), T(0x55595e), g, [0.015, 0.09, 0.172]);         // COOK lever
      // floral print band
      add(B.lathe([[0.1605, 0.07], [0.1615, 0.07], [0.1615, 0.13], [0.1605, 0.13]], 48), T(0xe9a7b8), g);
      g.userData.led = cookLed;
      return g;
    }
    function washer() {             // top-load, origin = floor centre
      const g = new THREE.Group(), W = 0.55, H = 0.9;
      add(rb(W, H, W, 0.04, 0.01), T(0xf4f5f3), g, [0, H / 2 + 0.03, 0]);
      add(rb(W - 0.02, 0.1, 0.06, 0.02), T(0xe6e8ea), g, [0, H + 0.08, -W / 2 + 0.05]);   // control panel (back top)
      [-0.15, -0.05, 0.05].forEach(x => add(new THREE.CylinderGeometry(0.012, 0.012, 0.01, 14), T(0x6a8fb5), g, [x, H + 0.1, -W / 2 + 0.081], [Math.PI / 2, 0, 0]));
      add(rb(0.08, 0.035, 0.006, 0.004), new THREE.MeshBasicMaterial({ color: 0x2f3a46 }), g, [0.17, H + 0.1, -W / 2 + 0.082]);
      add(rb(W - 0.06, 0.012, W - 0.16, 0.06), glass(0.55, 0x4a5560), g, [0, H + 0.04, 0.03]);  // tinted top lid
      return g;
    }
    function socket() {             // stopkontak (Schuko), origin = wall
      const g = new THREE.Group();
      add(rb(0.08, 0.08, 0.012, 0.008), T(0xf6f6f2), g, [0, 0, 0.006]);
      add(new THREE.CylinderGeometry(0.022, 0.022, 0.008, 28), T(0xe9e9e4), g, [0, 0, 0.012], [Math.PI / 2, 0, 0]);
      [-0.0095, 0.0095].forEach(x => add(new THREE.CylinderGeometry(0.0025, 0.0025, 0.002, 10), T(0x222222), g, [x, 0, 0.0165], [Math.PI / 2, 0, 0]));
      [0.017, -0.017].forEach(y => add(B.box(0.006, 0.004, 0.003), T(0xc9a227), g, [0, y, 0.0165]));   // earth clips
      return g;
    }
    function lightSwitch() {
      const g = new THREE.Group();
      add(rb(0.08, 0.08, 0.012, 0.008), T(0xf6f6f2), g, [0, 0, 0.006]);
      add(rb(0.03, 0.045, 0.008, 0.004), T(0xececE7), g, [0, 0, 0.014]);
      return g;
    }
    function ceilingLamp() {        // fitting plafon + LED bulb, origin = ceiling point (hangs down)
      const g = new THREE.Group();
      add(B.cyl(0.045, 0.03, 20), T(0xf6f6f2), g, [0, -0.015, 0]);
      add(B.cyl(0.018, 0.05, 14), T(0xf6f6f2), g, [0, -0.055, 0]);
      const bulbMat = T(0xfff6dc, { emissive: new THREE.Color(0xffd36b), emissiveIntensity: 0 });
      const bulb = add(new THREE.SphereGeometry(0.035, 18, 14), bulbMat, g, [0, -0.115, 0]);
      add(B.cyl(0.02, 0.03, 14), T(0xf2f2ee), g, [0, -0.085, 0]);
      g.userData.bulbMat = bulbMat;
      return g;
    }
    function hand() {               // relaxed hand reaching forward (-z), origin = wrist
      const g = new THREE.Group(), skin = T(0xe9b894);
      add(rb(0.085, 0.03, 0.1, 0.014, 0.008), skin, g, [0, 0, -0.05]);
      [-0.03, -0.01, 0.01, 0.03].forEach((x, i) => add(rb(0.017, 0.017, 0.075 - Math.abs(i - 1.5) * 0.008, 0.008, 0.004), skin, g, [x, -0.004, -0.13]));
      add(rb(0.018, 0.018, 0.055, 0.008, 0.004), skin, g, [-0.05, -0.002, -0.07], [0, 0.6, 0]);
      add(B.cyl(0.04, 0.3, 16), T(0x6b8fb8), g, [0, 0.005, 0.15], [Math.PI / 2, 0, 0]);   // sleeve
      return g;
    }
    return { kwhMeter, mcb, rccb, boxMcb, pole, earthRod, splitzen, acSplit, fridge, riceCooker, washer, socket, lightSwitch, ceilingLamp, hand, tex };
  }
  B.listrik = S => make(S);
})();
