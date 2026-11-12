// BEDAH.lift: reusable lifting / lift (elevator) parts, modelled from reference photos
// (projects/lift-bongkar/refs/SPEK.md). Units: metres, front = +z, brand-free.
// Each builder returns a THREE.Group; its origin is noted per item. Moving parts are in .userData.
(function () {
  const B = window.BEDAH;

  function make(S) {
    const { stage, THREE } = S, { add, scene } = stage;
    const T = (hex, ex) => stage.toon(hex, false, ex);
    const rb = (w, h, d, r, bev = 0.004) => B.rbox(w, h, d, Math.min(r, w / 2 - 1e-4, h / 2 - 1e-4), 1, bev);
    const tex = (w, h, draw) => { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
      const t = new THREE.CanvasTexture(c); t.anisotropy = 4; return t; };
    const COL = { steel: 0x8d949b, dark: 0x4f555b, zinc: 0xbcc4ca, wood: 0xb47f52, woodDark: 0x8a5a36, hemp: 0xc9a46b,
      wire: 0x9ea6ad, yellow: 0xf2c230, motor: 0x3f78b5, concrete: 0xc9c3b8, brass: 0xd08a3a, cabin: 0xece4d4,
      stainless: 0xd3d8dc, skin: 0xe9b894, shirt: 0x5d8bc4, pants: 0x3a4250, hair: 0x2b2522 };
    const M = {};
    const mat = k => M[k] || (M[k] = T(COL[k]));
    const ALONG_Z = [Math.PI / 2, 0, 0];

    // twisted-rope texture (diagonal lay); hemp or steel wire rope
    const ropeTex = {
      hemp: tex(32, 64, (c, w, h) => { c.fillStyle = '#c9a46b'; c.fillRect(0, 0, w, h); c.strokeStyle = '#9c7a45'; c.lineWidth = 5;
        for (let i = -2; i < 4; i++) { c.beginPath(); c.moveTo(0, i * 24); c.lineTo(w, i * 24 + 24); c.stroke(); } }),
      wire: tex(32, 64, (c, w, h) => { c.fillStyle = '#a7aeb4'; c.fillRect(0, 0, w, h); c.strokeStyle = '#6f777e'; c.lineWidth = 3;
        for (let i = -2; i < 6; i++) { c.beginPath(); c.moveTo(0, i * 14); c.lineTo(w, i * 14 + 18); c.stroke(); } }),
    };
    Object.values(ropeTex).forEach(t => { t.wrapS = t.wrapT = THREE.RepeatWrapping; });

    // ------------------------------------------------------------ rope pieces
    // rope(r, kind): straight piece between two points, .userData.set(a, b) every frame (a, b = [x,y,z])
    function rope(r = 0.012, kind = 'hemp', parent) {
      const map = ropeTex[kind].clone(); map.needsUpdate = true;
      const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 1, 10, 1, true), T(0xffffff, { map }));
      m.castShadow = true;
      const up = new THREE.Vector3(0, 1, 0), A = new THREE.Vector3(), D = new THREE.Vector3();
      m.userData.set = (a, b) => {
        A.set(a[0], a[1], a[2]); D.set(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
        const L = D.length(); m.visible = L > 0.003; if (!m.visible) return m;
        m.position.copy(A).addScaledVector(D, 0.5); m.quaternion.setFromUnitVectors(up, D.normalize());
        m.scale.set(1, L, 1); map.repeat.set(1, L / (r * 6)); return m;
      };
      (parent || scene).add(m);
      return m;
    }
    // ropeArc(R, r, a0, a1): rope lying in a sheave groove (xy plane, around the axle), angles in radians (0 = +x)
    function ropeArc(R, r, a0, a1, kind = 'hemp', parent) {
      const map = ropeTex[kind].clone(); map.needsUpdate = true; map.repeat.set(R * (a1 - a0) / (r * 6), 1);
      const m = new THREE.Mesh(new THREE.TorusGeometry(R, r, 8, 28, a1 - a0), T(0xffffff, { map }));
      m.rotation.z = a0; m.castShadow = true; (parent || scene).add(m); return m;
    }

    // ------------------------------------------------------------ zinc bucket (origin: bottom centre; .userData.hook = handle top)
    function bucket() {
      const g = new THREE.Group(), zinc = T(COL.zinc, { side: THREE.DoubleSide, metalness: 0.1, roughness: 0.45 });
      const prof = [[0.0, 0.0], [0.12, 0.0], [0.122, 0.012], [0.15, 0.28]].map(([x, y]) => new THREE.Vector2(x, y));
      add(new THREE.LatheGeometry(prof, 40), zinc, g);
      add(new THREE.TorusGeometry(0.151, 0.007, 8, 40), zinc, g, [0, 0.282, 0], [Math.PI / 2, 0, 0]);          // rolled rim
      [0.09, 0.19].forEach(y => add(new THREE.TorusGeometry(0.12 + 0.03 * y / 0.28 + 0.002, 0.004, 6, 40), zinc, g, [0, y, 0], [Math.PI / 2, 0, 0]));   // ribs
      const water = add(new THREE.CircleGeometry(0.138, 32), T(0x7fb6d9, { transparent: true, opacity: 0.85 }), g, [0, 0.215, 0], [-Math.PI / 2, 0, 0]);
      const handle = new THREE.Group(); handle.position.set(0, 0.27, 0); g.add(handle);
      add(new THREE.TorusGeometry(0.152, 0.004, 6, 40, Math.PI), mat('dark'), handle);                           // wire bail
      add(B.cyl(0.012, 0.09, 12), mat('wood'), handle, [0, 0.152, 0], [0, 0, Math.PI / 2]);                     // wooden grip
      [-1, 1].forEach(s => add(B.cyl(0.012, 0.006, 10), zinc, g, [s * 0.146, 0.27, 0], [0, 0, Math.PI / 2]));      // ears
      g.userData = { hook: [0, 0.27 + 0.165, 0], water };
      return g;
    }

    // ------------------------------------------------------------ wooden pulley block (origin: axle; rope radius .userData.r)
    function woodPulley() {
      const g = new THREE.Group(), wheel = new THREE.Group(); g.add(wheel);
      const prof = [[0.02, -0.022], [0.125, -0.022], [0.125, -0.012], [0.1, 0], [0.125, 0.012], [0.125, 0.022], [0.02, 0.022]].map(([x, y]) => new THREE.Vector2(x, y));
      add(new THREE.LatheGeometry(prof, 36), mat('wood'), wheel, null, ALONG_Z);
      [0, 1, 2].forEach(i => add(B.box(0.2, 0.012, 0.03), mat('woodDark'), wheel, [0, 0, 0], [0, 0, i * Math.PI / 3]));    // spokes
      add(B.cyl(0.018, 0.1, 14), mat('dark'), g, null, ALONG_Z);                                                 // axle pin
      [-1, 1].forEach(s => add(rb(0.075, 0.34, 0.016, 0.03, 0.004), mat('woodDark'), g, [0, 0.05, s * 0.034]));  // cheeks
      add(rb(0.08, 0.05, 0.085, 0.01), mat('woodDark'), g, [0, 0.2, 0]);                                         // crown
      add(B.box(0.03, 0.12, 0.09), mat('dark'), g, [0, 0.27, 0]);                                                 // iron strap
      add(new THREE.TorusGeometry(0.035, 0.008, 8, 20), mat('dark'), g, [0, 0.35, 0]);                              // hook eye
      g.userData = { wheel, r: 0.1 };
      return g;
    }

    // ------------------------------------------------------------ traction machine (origin: sheave axle; sheave in xy plane, motor behind -z)
    function machine(o = {}) {
      const g = new THREE.Group(), R = o.r ?? 0.25, wheel = new THREE.Group(); g.add(wheel);
      const prof = [[0.05, -0.07], [R + 0.03, -0.07]];
      for (let i = 0; i < 5; i++) { const z = -0.055 + i * 0.0275; prof.push([R + 0.03, z - 0.008], [R, z], [R + 0.03, z + 0.008]); }
      prof.push([R + 0.03, 0.07], [0.05, 0.07]);
      add(new THREE.LatheGeometry(prof.map(([x, y]) => new THREE.Vector2(x, y)), 48), T(0x9aa2a8, { metalness: 0.1, roughness: 0.4 }), wheel, null, ALONG_Z);
      add(B.cyl(R * 0.55, 0.15, 32), mat('yellow'), wheel, null, ALONG_Z);                                       // hub disc
      [0, 1, 2, 3].forEach(i => add(B.cyl(0.018, 0.155, 10), mat('dark'), wheel, [Math.cos(i * Math.PI / 2) * R * 0.32, Math.sin(i * Math.PI / 2) * R * 0.32, 0], ALONG_Z));
      const motor = new THREE.Group(); motor.position.z = -0.09; g.add(motor);
      add(B.cyl(R + 0.08, 0.42, 36), mat('motor'), motor, [0, 0, -0.22], ALONG_Z);
      for (let i = 0; i < 6; i++) add(B.cyl(R + 0.095, 0.018, 36), T(0x356aa2), motor, [0, 0, -0.06 - i * 0.065], ALONG_Z);   // cooling ribs
      add(B.cyl(R * 0.7, 0.08, 28), mat('dark'), motor, [0, 0, -0.47], ALONG_Z);                                  // brake drum cover
      [-1, 1].forEach(s => add(rb(0.08, 0.26, 0.1, 0.02), mat('dark'), motor, [s * (R + 0.04), -0.08, -0.47]));    // brake arms
      add(rb(0.12, 0.1, 0.1, 0.02), mat('yellow'), motor, [0, R + 0.11, -0.34]);                                  // terminal box
      add(rb(R * 2 + 0.36, 0.08, 0.7, 0.02), mat('dark'), g, [0, -R - 0.12, -0.27]);                               // bedplate
      [-1, 1].forEach(s => add(rb(0.08, R + 0.06, 0.5, 0.02), mat('dark'), g, [s * (R + 0.12), -R / 2 - 0.06, -0.27]));
      g.userData = { wheel, motor, r: R, foot: -R - 0.16 };
      return g;
    }

    // plain sheave (idler / deflector / pulley), origin axle; o.r rope radius, o.color
    function sheave(o = {}) {
      const g = new THREE.Group(), R = o.r ?? 0.18, wheel = new THREE.Group(); g.add(wheel);
      const prof = [[0.04, -0.05], [R + 0.025, -0.05], [R + 0.025, -0.03], [R, 0], [R + 0.025, 0.03], [R + 0.025, 0.05], [0.04, 0.05]];
      add(new THREE.LatheGeometry(prof.map(([x, y]) => new THREE.Vector2(x, y)), 40), T(o.color ?? 0x9aa2a8, { metalness: 0.1, roughness: 0.45 }), wheel, null, ALONG_Z);
      [0, 1, 2].forEach(i => add(B.box(R * 1.9, 0.03, 0.04), mat('dark'), wheel, [0, 0, 0], [0, 0, i * Math.PI / 3]));
      add(B.cyl(0.035, 0.16, 14), mat('dark'), g, null, ALONG_Z);
      if (o.stand !== false) [-1, 1].forEach(s => add(rb(0.05, R + 0.25, 0.03, 0.01), mat('dark'), g, [0, -(R + 0.25) / 2 + 0.05, s * 0.075]));
      g.userData = { wheel, r: R };
      return g;
    }

    // ------------------------------------------------------------ guide rail, T profile (origin: bottom, flange back face at x = 0;
    // dir = +1 blade points +x, -1 points -x). Brackets every o.every metres reaching back to o.wall (local x of the wall face) or -z.
    function rail(len, dir = 1, o = {}) {
      const g = new THREE.Group();
      add(B.box(0.016, len, 0.09), T(0x5a6066), g, [dir * 0.008, len / 2, 0]);                                     // flange
      add(B.box(0.065, len, 0.016), T(0x5a6066), g, [dir * (0.016 + 0.0325), len / 2, 0]);                          // blade
      add(B.box(0.004, len, 0.017), T(0xb7c0c7, { metalness: 0.1, roughness: 0.3 }), g, [dir * (0.016 + 0.065), len / 2, 0]);   // machined face
      const every = o.every ?? 2.2;
      for (let y = 0.6; y < len; y += every) {
        if (o.wall !== undefined) {
          const w = Math.abs(o.wall); add(B.box(w, 0.12, 0.12), T(0x6a7076), g, [-dir * w / 2, y, 0]);
        } else if (o.back !== undefined) {
          add(B.box(0.12, 0.12, o.back), T(0x6a7076), g, [0, y, -o.back / 2 - 0.045]);
        }
        add(B.box(0.03, 0.14, 0.13), T(0x6a7076), g, [-dir * 0.015, y, 0]);                                       // clip plate
      }
      return g;
    }

    // ------------------------------------------------------------ lift car with sling, guide shoes and safety gear
    // origin: cabin floor top, centre. Rail blade faces expected at x = ±o.railX (blade x ∈ [railX, railX+0.065]), z = 0.
    function car(o = {}) {
      const g = new THREE.Group(), W = 1.1, D = 1.4, H = 2.3, rx = o.railX ?? 0.8;
      const wall = T(COL.cabin), outer = T(0xc3c8cc, { metalness: 0.2, roughness: 0.5 });
      add(rb(W + 0.06, 0.08, D + 0.04, 0.01), outer, g, [0, -0.04, 0]);                                       // floor
      add(B.box(W - 0.02, 0.006, D - 0.02), T(0x8f8478), g, [0, 0.003, 0]);                                    // floor finish
      add(rb(W + 0.06, 0.06, D + 0.04, 0.01), outer, g, [0, H + 0.03, 0]);                                     // roof
      add(B.box(W, 0.04, D), wall, g, [0, H - 0.02, 0]);
      const light = add(B.box(0.6, 0.012, 0.6), T(0xfff6d8, { emissive: 0xfff2c8, emissiveIntensity: 0.6 }), g, [0, H - 0.045, 0]);
      add(B.box(W, H, 0.04), wall, g, [0, H / 2, -D / 2 + 0.02]);                                              // back wall
      [-1, 1].forEach(s => add(B.box(0.04, H, D), wall, g, [s * (W / 2 - 0.02), H / 2, 0]));                     // side walls
      [-1, 1].forEach(s => add(B.box(0.045, H, D + 0.02), outer, g, [s * (W / 2 + 0.01), H / 2, 0]));          // outer skin
      add(B.box(W * 0.8, 0.035, 0.05), T(0xb9bec2, { metalness: 0.1, roughness: 0.3 }), g, [0, 0.95, -D / 2 + 0.08]);   // handrail
      // car operating panel (inside, front right)
      add(B.box(0.02, 0.6, 0.18), T(0xc9ced2, { metalness: 0.1 }), g, [W / 2 - 0.05, 1.25, D / 2 - 0.22]);
      for (let i = 0; i < 4; i++) add(B.cyl(0.013, 0.01, 14), T(0xfff2b0, { emissive: 0xffd84a, emissiveIntensity: 0.25 }), g, [W / 2 - 0.065, 1.05 + i * 0.1, D / 2 - 0.22], [0, 0, Math.PI / 2]);
      // front: returns + two door panels (hidden in cutaway shots: g.userData.front.visible)
      const front = new THREE.Group(); g.add(front);
      [-1, 1].forEach(s => add(B.box(0.15, H, 0.05), outer, front, [s * (W / 2 - 0.075), H / 2, D / 2]));
      add(B.box(W, 0.25, 0.05), outer, front, [0, H - 0.125, D / 2]);
      const doors = [-1, 1].map(s => { const d = add(B.box(0.4, 2.05, 0.03), T(COL.stainless, { metalness: 0.1, roughness: 0.3 }), front, [s * 0.2, 1.025, D / 2 + 0.03]); d.userData.x0 = s * 0.2; d.userData.s = s; return d; });
      // sling (car frame): crosshead, stiles, plank (dark steel)
      const fr = T(0x3c4248);
      add(B.box(rx * 2 - 0.08, 0.16, 0.18), fr, g, [0, H + 0.32, 0]);                                         // crosshead
      [-1, 1].forEach(s => add(B.box(0.1, H + 0.75, 0.16), fr, g, [s * (rx - 0.09), H / 2 + 0.04, 0]));          // stiles
      add(B.box(rx * 2 - 0.08, 0.16, 0.3), fr, g, [0, -0.17, 0]);                                              // safety plank
      // rope hitch (shackles + springs) on the crosshead
      const hitch = new THREE.Group(); hitch.position.set(0, H + 0.4, 0); g.add(hitch);
      for (let i = 0; i < 4; i++) add(B.coil(0.022, 0.1, 5, 0.006), T(0xd9a13a), hitch, [(i - 1.5) * 0.05, 0.03, 0]);
      add(B.box(0.24, 0.025, 0.08), fr, hitch, [0, 0.0, 0]);
      // guide shoes top + bottom on each stile (U around the blade)
      [-1, 1].forEach(s => [H + 0.3, -0.2].forEach(y => {
        add(B.box(0.09, 0.14, 0.12), T(0x2f3439), g, [s * (rx - 0.045), y, 0]);
        [-1, 1].forEach(zs => add(B.box(0.05, 0.1, 0.035), T(0x111417), g, [s * (rx + 0.03), y, zs * 0.036]));   // pads either side of the blade
      }));
      // safety gear housing + wedge jaws under each stile, both sides of the blade
      const jaws = [];
      [-1, 1].forEach(s => {
        add(B.box(0.08, 0.22, 0.2), T(0x2f3439), g, [s * (rx - 0.04), -0.42, 0]);
        [-1, 1].forEach(zs => add(B.box(0.1, 0.22, 0.03), T(0x2f3439), g, [s * (rx + 0.04), -0.42, zs * 0.085]));   // cheeks around the blade
        [-1, 1].forEach(zs => { const j = add(rb(0.06, 0.12, 0.03, 0.006), T(COL.brass, { metalness: 0.1, roughness: 0.4 }), g, [s * (rx + 0.035), -0.44, zs * 0.045]);
          j.userData = { z0: zs * 0.045, y0: -0.44, zs }; jaws.push(j); });
      });
      // linkage: pull rod up the left stile + cross rod under the plank + lever at the top (governor rope clamp)
      const link = new THREE.Group(); g.add(link);
      add(B.cyl(0.012, H + 0.95, 10), mat('yellow'), link, [-(rx - 0.15), H / 2 - 0.08, 0.13]);
      add(B.cyl(0.012, rx * 2 - 0.1, 10), mat('yellow'), link, [0, -0.36, 0.13], [0, 0, Math.PI / 2]);
      const lever = new THREE.Group(); lever.position.set(-(rx - 0.15), H + 0.4, 0.13); link.add(lever);
      add(B.box(0.24, 0.035, 0.035), mat('yellow'), lever, [-0.1, 0, 0]);
      add(B.box(0.05, 0.08, 0.06), T(0x2f3439), lever, [-0.21, 0, 0]);                                         // rope clamp
      g.userData = { W, D, H, rx, front, doors, jaws, link, lever, light, hitchY: H + 0.42,
        govAttach: [-(rx - 0.15) - 0.21, H + 0.4, 0.13],
        setDoors(k) { doors.forEach(d => { d.position.x = d.userData.x0 + d.userData.s * k * 0.4; }); },
        setGrip(k) { jaws.forEach(j => { j.position.y = j.userData.y0 + 0.06 * k; j.position.z = j.userData.z0 - j.userData.zs * 0.02 * k; }); } };
      return g;
    }

    // ------------------------------------------------------------ counterweight (origin: bottom centre; hitch at top)
    function counterweight(o = {}) {
      const g = new THREE.Group(), W = o.w ?? 0.55, H = o.h ?? 2.4, D = 0.2, fr = T(0x3c4248);
      [-1, 1].forEach(s => add(B.box(0.06, H, D), fr, g, [s * (W / 2 - 0.03), H / 2, 0]));
      add(B.box(W, 0.12, D + 0.02), fr, g, [0, H - 0.06, 0]);
      add(B.box(W, 0.1, D + 0.02), fr, g, [0, 0.05, 0]);
      const n = Math.floor((H - 0.26) / 0.17);
      for (let i = 0; i < n; i++) add(rb(W - 0.13, 0.15, D - 0.03, 0.01, 0.006), T(i % 2 ? 0xb8b2a6 : 0xc4beb2), g, [0, 0.12 + 0.085 + i * 0.17, 0]);
      add(B.box(0.04, H - 0.2, 0.03), fr, g, [0, H / 2, D / 2 + 0.01]);                                          // tie rod
      [-1, 1].forEach(s => [H - 0.12, 0.1].forEach(y => add(B.box(0.08, 0.12, 0.1), T(0x2f3439), g, [s * (W / 2 + 0.03), y, 0])));
      for (let i = 0; i < 4; i++) add(B.coil(0.02, 0.09, 5, 0.005), T(0xd9a13a), g, [(i - 1.5) * 0.045, H + 0.05, 0]);
      g.userData = { W, H, hitchY: H + 0.12 };
      return g;
    }

    // ------------------------------------------------------------ overspeed governor (origin: axle; yellow sheave, flyweights, latch)
    function governor(o = {}) {
      const g = new THREE.Group(), R = o.r ?? 0.15, wheel = new THREE.Group(); g.add(wheel);
      const prof = [[0.03, -0.035], [R + 0.03, -0.035], [R + 0.03, -0.015], [R, 0], [R + 0.03, 0.015], [R + 0.03, 0.035], [0.03, 0.035]];
      add(new THREE.LatheGeometry(prof.map(([x, y]) => new THREE.Vector2(x, y)), 40), mat('yellow'), wheel, null, ALONG_Z);
      [0, 1, 2, 3, 4].forEach(i => add(B.box(R * 1.9, 0.02, 0.03), T(0xd9a821), wheel, [0, 0, 0.0], [0, 0, i * Math.PI / 5]));
      const weights = [-1, 1].map(s => { const p = new THREE.Group(); p.position.set(0, 0, 0.05); wheel.add(p);
        add(B.box(0.012, 0.09, 0.012), mat('dark'), p, [s * 0.02, s * 0.045, 0]);
        add(rb(0.05, 0.035, 0.03, 0.008), T(0xc8322b), p, [s * 0.03, s * 0.09, 0]); p.userData.s = s; return p; });
      add(B.cyl(0.025, 0.14, 12), mat('dark'), g, null, ALONG_Z);
      [-1, 1].forEach(s => add(rb(0.05, R + 0.32, 0.025, 0.01), mat('dark'), g, [0, -(R + 0.32) / 2 + 0.03, s * 0.06]));
      add(rb(R * 2 + 0.2, 0.05, 0.22, 0.01), mat('dark'), g, [0, -R - 0.28, 0]);
      const latch = new THREE.Group(); latch.position.set(R + 0.07, R * 0.4, 0.05); g.add(latch);           // pawl that locks the sheave
      add(rb(0.03, 0.14, 0.03, 0.006), T(0xc8322b), latch, [0, -0.06, 0]);
      g.userData = { wheel, weights, latch, r: R,
        setFly(k) { weights.forEach(p => { p.rotation.z = p.userData.s * 0.5 * k; }); },
        setLatch(k) { latch.rotation.z = -0.6 * (1 - k); } };
      g.userData.setLatch(0);
      return g;
    }

    // tension pulley in the pit with its hanging weight (origin: axle)
    function tensionPulley(o = {}) {
      const g = sheave({ r: o.r ?? 0.12, stand: false, color: 0xf2c230 });
      add(rb(0.04, 0.5, 0.03, 0.008), mat('dark'), g, [0.12, -0.12, 0.05], [0, 0, 0.5]);
      add(rb(0.14, 0.18, 0.1, 0.02), mat('dark'), g, [0.25, -0.32, 0.05]);
      add(rb(0.05, 0.3, 0.12, 0.01), mat('dark'), g, [-0.2, -0.1, 0]);
      return g;
    }

    // ------------------------------------------------------------ people
    // person standing (origin: between the feet, facing +z), ~1.65 m
    function person(o = {}) {
      const g = new THREE.Group(), shirt = T(o.shirt ?? COL.shirt), pants = T(o.pants ?? COL.pants), skin = T(COL.skin);
      [-1, 1].forEach(s => {
        add(new THREE.CapsuleGeometry(0.06, 0.66, 4, 10), pants, g, [s * 0.09, 0.45, 0]);
        add(rb(0.1, 0.06, 0.24, 0.025), T(0x2b2522), g, [s * 0.09, 0.03, 0.04]);
      });
      add(new THREE.CapsuleGeometry(0.17, 0.36, 4, 14), shirt, g, [0, 1.12, 0]).scale.set(1, 1, 0.65);
      const arms = [-1, 1].map(s => { const a = new THREE.Group(); a.position.set(s * 0.21, 1.36, 0); g.add(a);
        add(new THREE.CapsuleGeometry(0.05, 0.5, 4, 10), shirt, a, [0, -0.3, 0]);
        add(new THREE.SphereGeometry(0.05, 12, 10), skin, a, [0, -0.6, 0]); return a; });
      add(B.cyl(0.05, 0.08, 12), skin, g, [0, 1.48, 0]);
      add(new THREE.SphereGeometry(0.12, 20, 16), skin, g, [0, 1.6, 0]).scale.set(0.92, 1.05, 1);
      add(new THREE.SphereGeometry(0.125, 20, 12, 0, Math.PI * 2, 0, Math.PI * 0.55), T(COL.hair), g, [0, 1.62, -0.01]);
      [-1, 1].forEach(s => add(new THREE.SphereGeometry(0.012, 8, 6), T(0x2b2522), g, [s * 0.04, 1.62, 0.108]));
      g.userData = { arms };
      return g;
    }
    // fist gripping a rope that runs along local y through it; the arm comes from +x (origin: grip centre)
    function fist(o = {}) {
      const g = new THREE.Group(), skin = T(COL.skin);
      add(rb(0.09, 0.1, 0.08, 0.03, 0.01), skin, g, [0.015, 0, 0]);
      [-0.03, -0.01, 0.01, 0.03].forEach(y => add(new THREE.CapsuleGeometry(0.014, 0.03, 4, 8), skin, g, [-0.035, y, 0.02], [0, 0, Math.PI / 2]));
      add(new THREE.CapsuleGeometry(0.015, 0.04, 4, 8), skin, g, [-0.02, 0.045, -0.03], [0.4, 0, 0.9]);
      add(B.cyl(0.045, 0.32, 16), T(o.sleeve ?? 0x6b8fb8), g, [0.2, 0, 0], [0, 0, Math.PI / 2]);
      return g;
    }

    return { rope, ropeArc, bucket, woodPulley, machine, sheave, rail, car, counterweight, governor, tensionPulley, person, fist, tex, COL };
  }
  B.lift = S => make(S);
})();
