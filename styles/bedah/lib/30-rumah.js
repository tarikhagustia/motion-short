// BEDAH.rumah(S, opts): reusable Indonesian perumahan house (1 storey, gable roof with clay tiles facing
// the street), modelled from reference photos (projects/listrik-rumah-aman/refs). Units: metres.
// Dollhouse cutaway: everything in front of z = cut is removed (setCut(rumah.cut) each frame), so the
// camera looks into three rooms side by side (L kamar, M ruang tengah, R dapur). The roof + ceiling are
// one lid that can lift off (rumah.lift(k)) for top-down shots. The soil block is cut open at the front.
(function () {
  const B = window.BEDAH;
  B.rumah = function (S, o = {}) {
    const { stage, THREE } = S, { add } = stage;
    const T = (hex, clip = true, extra) => stage.toon(hex, clip, extra);
    const L = B.listrik(S);
    const tile = (w, h, draw, rx, ry) => { const t = L.tex(w, h, draw); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx, ry); return t; };
    // textures
    const keramik = tile(128, 128, (c, w, h) => { c.fillStyle = '#ece6dc'; c.fillRect(0, 0, w, h); c.strokeStyle = '#cfc6b8'; c.lineWidth = 3; c.strokeRect(0, 0, w, h);
      c.fillStyle = 'rgba(255,255,255,.25)'; c.fillRect(8, 8, 50, 20); }, 7 / 0.4, 8 / 0.4);
    const genteng = (len, wid) => tile(128, 128, (c, w, h) => { c.fillStyle = '#c4643d'; c.fillRect(0, 0, w, h);
      for (let i = 0; i < 4; i++) { c.fillStyle = i % 2 ? '#b5573a' : '#cf7048'; c.fillRect(i * 32, 0, 30, h); c.fillStyle = 'rgba(0,0,0,.18)'; c.fillRect(i * 32 + 28, 0, 4, h); }
      c.fillStyle = 'rgba(0,0,0,.22)'; c.fillRect(0, h - 10, w, 10); c.fillStyle = 'rgba(255,255,255,.12)'; c.fillRect(0, 0, w, 6); }, len / 0.32, wid / 0.3);
    const M = {
      wallOut: T(0xf0e6d2), wallIn: T(0xf6f0e6), floor: T(0xffffff, true, { map: keramik }), skirting: T(0xbfae98),
      ceiling: T(0xfbfaf6, false), wood: T(0xa9774d, false), woodClip: T(0xa9774d), lisplang: T(0xf4f1ea, false),
      soil: T(0x8f6446), soilDk: T(0x765238, false), grass: T(0x8fbf6a), glass: T(0xbfd9e6, true, { transparent: true, opacity: 0.45, depthWrite: false }),
      frame: T(0x8a5b38), sill: T(0xd8cdbd), concrete: T(0xbab6ad),
    };
    const g = new THREE.Group(); stage.scene.add(g);
    const X0 = -3.5, X1 = 3.5, Z0 = -4, Z1 = 4, F = 0.2, H = 3.0, TOP = F + H, th = 0.15;
    const cut = o.cut ?? 3.0;

    // ground: soil block (open at the front cut) + grass + soil layers & stones on the back face
    add(B.box(26, 2.6, 16), M.soil, g, [0, -1.33, -3]);
    add(B.box(26, 0.06, 16), M.grass, g, [0, -0.02, -3]);
    [[-0.8, 0x845a3e], [-1.7, 0x6f4a32]].forEach(([y, c]) => add(B.box(25.6, 0.4, 0.06), T(c, false), g, [0, y, -10.9]));
    for (let i = 0; i < 14; i++) add(new THREE.SphereGeometry(0.08 + B.hash(i) * 0.1, 10, 8), M.soilDk, g, [-10 + i * 1.5, -0.5 - B.hash(i + 4) * 1.8, -10.7]);

    // floor slab with keramik
    add(B.box(X1 - X0 + 0.3, F, Z1 - Z0 + 0.3), M.floor, g, [0, F / 2, 0]);

    // walls with openings: wall(axis, fixed, a0, a1, holes [[u0,u1,v0,v1]], mat)
    function wall(axis, fixed, a0, a1, holes = [], mat = M.wallOut, t = th) {
      const piece = (u0, u1, v0, v1) => { if (u1 - u0 < 0.001 || v1 - v0 < 0.001) return;
        const cu = (u0 + u1) / 2, cv = (v0 + v1) / 2;
        if (axis === 'x') add(B.box(u1 - u0, v1 - v0, t), mat, g, [cu, cv, fixed]);
        else add(B.box(t, v1 - v0, u1 - u0), mat, g, [fixed, cv, cu]); };
      let c = a0;
      holes.slice().sort((p, q) => p[0] - q[0]).forEach(([u0, u1, v0, v1]) => {
        piece(c, u0, F, TOP); piece(u0, u1, F, v0); piece(u0, u1, v1, TOP); c = u1;
        // kusen (frame) + glass for windows (v0 > F), frame only for doors
        const fw = 0.06, fd = t + 0.04;
        const fr = (cu, cv, w, h) => { if (axis === 'x') add(B.box(w, h, fd), M.frame, g, [cu, cv, fixed]); else add(B.box(fd, h, w), M.frame, g, [fixed, cv, cu]); };
        fr((u0 + u1) / 2, v1 - fw / 2, u1 - u0, fw); fr(u0 + fw / 2, (v0 + v1) / 2, fw, v1 - v0); fr(u1 - fw / 2, (v0 + v1) / 2, fw, v1 - v0);
        if (v0 > F + 0.01) {
          fr((u0 + u1) / 2, v0 + fw / 2, u1 - u0, fw); fr((u0 + u1) / 2, (v0 + v1) / 2, fw, v1 - v0);   // sill + mullion
          if (axis === 'x') add(B.box(u1 - u0 - 0.1, v1 - v0 - 0.1, 0.01), M.glass, g, [(u0 + u1) / 2, (v0 + v1) / 2, fixed]);
          else add(B.box(0.01, v1 - v0 - 0.1, u1 - u0 - 0.1), M.glass, g, [fixed, (v0 + v1) / 2, (u0 + u1) / 2]);
        }
      });
      piece(c, a1, F, TOP);
    }
    wall('x', Z0, X0 - th / 2, X1 + th / 2, [[-0.4, 0.2, 1.0, 2.1]]);                          // back wall (small window, ruang tengah)
    wall('z', X0, Z0, Z1, [[-2.6, -1.4, 1.0, 2.2], [0.6, 1.8, 1.0, 2.2]]);                    // left wall (kamar windows)
    wall('z', X1, Z0, Z1, [[-2.6, -1.8, 1.2, 2.1], [0.3, 1.5, 1.0, 2.2]]);                    // right wall (dapur window, front window)
    const XI = o.inner ?? [-1.0, 1.5];
    XI.forEach(x => wall('z', x, Z0, 1.0, [[-0.2, 0.7, F, 2.3]], M.wallIn, 0.12));           // partitions with door openings
    // skirting
    add(B.box(X1 - X0, 0.1, 0.03), M.skirting, g, [0, F + 0.05, Z0 + th / 2 + 0.015]);
    // exterior plinth
    add(B.box(X1 - X0 + 0.34, 0.25, Z1 - Z0 + 0.34), M.concrete, g, [0, 0.08, 0]);

    // ---------------- lid: ceiling + lamps + roof (trusses, clay-tile slopes, gable, fascia)
    const lid = new THREE.Group(); g.add(lid);
    const lidMats = [];
    const LT = (hex, ex) => { const m = T(hex, true, ex); lidMats.push(m); return m; };
    add(B.box(X1 - X0, 0.04, Z1 - Z0), LT(0xfbfaf6), lid, [0, TOP + 0.02, 0]);                    // plafon (gypsum)
    add(B.box(X1 - X0, 0.08, 0.04), LT(0xeae4d8), lid, [0, TOP - 0.04, Z0 + 0.09]);               // list plafon
    const ridgeY = TOP + 1.9, ov = 0.5, ovz = 0.45;
    const run = (X1 - X0) / 2 + ov, rise = ridgeY - (TOP - 0.2);
    const slopeW = Math.hypot(run, rise), ang = Math.atan2(rise, run), len = Z1 - Z0 + 2 * ovz;
    [-1, 1].forEach(sd => {
      const slab = add(B.box(slopeW, 0.12, len), LT(0xffffff, { map: genteng(len, slopeW) }), lid);
      slab.position.set(sd * run / 2, (ridgeY + TOP - 0.2) / 2 + 0.06, 0); slab.rotation.z = -sd * ang;
      const fas = add(B.box(0.03, 0.22, len), LT(0xf4f1ea), lid, [sd * (run + 0.0), TOP - 0.25, 0]);   // lisplang
    });
    add(B.box(0.28, 0.16, len), LT(0xb5573a), lid, [0, ridgeY + 0.08, 0]);                           // nok (ridge tiles)
    // trusses (kuda-kuda) every 1.6 m
    for (let z = Z0 + 0.3; z < Z1; z += 1.6) {
      add(B.box(X1 - X0, 0.12, 0.08), LT(0xa9774d), lid, [0, TOP + 0.1, z]);
      [-1, 1].forEach(sd => { const r = add(B.box(Math.hypot(3.5, 1.8), 0.1, 0.08), LT(0xa9774d), lid); r.position.set(sd * 1.75, TOP + 0.1 + 0.9, z); r.rotation.z = -sd * Math.atan2(1.8, 3.5); });
      add(B.box(0.08, 1.8, 0.08), LT(0xa9774d), lid, [0, TOP + 1.0, z]);
    }
    // back gable wall
    const gable = B.polyShape([[X0 - 0.07, 0], [0, ridgeY - TOP], [X1 + 0.07, 0]]);
    add(new THREE.ExtrudeGeometry(gable, { depth: th, bevelEnabled: false }), LT(0xf0e6d2), lid, [0, TOP, Z0 - th / 2]);

    // ---------------- rooms: centres, ceiling lamps, darkness volumes
    const roomsX = { L: [X0, XI[0]], M: [XI[0], XI[1]], R: [XI[1], X1] };
    const rooms = {};
    Object.entries(roomsX).forEach(([k, [a, b]]) => {
      const cx = (a + b) / 2;
      const lamp = L.ceilingLamp(); lamp.position.set(cx, TOP, o.lampZ ?? 2.3); lid.add(lamp);
      const darkMat = new THREE.MeshBasicMaterial({ color: 0x1b2232, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide, clippingPlanes: stage.planes });
      const dark = new THREE.Mesh(B.box(b - a - 0.14, H - 0.02, Z1 - Z0 - 0.2), darkMat);
      dark.position.set(cx, F + H / 2, 0); dark.renderOrder = 5; g.add(dark);
      rooms[k] = { cx, x0: a, x1: b, lamp, bulbMat: lamp.userData.bulbMat, darkMat };
    });
    const pick = n => n === 'all' ? Object.values(rooms) : [rooms[n]];
    const light = (n, k) => pick(n).forEach(r => { r.bulbMat.emissiveIntensity = 2.2 * k; });
    const darkness = (n, k) => pick(n).forEach(r => { r.darkMat.opacity = 0.6 * k; });
    // lift(k): 0 = roof + ceiling on, 1 = lifted off (top-down shots)
    const lift = k => { lid.position.y = k * 7; lid.visible = k < 0.999; };

    const A = {
      F, TOP, ridgeY, X0, X1, Z0, Z1, XI,
      meterWall: [X1 + th / 2, F + 1.55, 2.3],            // kWh meter on the right outer wall (faces +x)
      bracket: [X1 + th / 2 + 0.05, TOP - 0.15, 2.75],     // SR cable anchor under the eave
      box: [0.3, F + 1.45, Z0 + th / 2],                   // box MCB on the back wall of the ruang tengah (faces +z)
      ac: [-2.25, F + 2.0, Z0 + th / 2],                   // AC on the kamar back wall
      fridge: [3.05, F, Z0 + 0.42],
      counter: [2.15, F, Z0 + 0.35],
      washer: [1.05, F, Z0 + 0.42],
      washerSocket: [0.65, F + 1.1, Z0 + th / 2],
      cordSocket: [-1.6, F + 0.35, Z0 + th / 2],
      gndRod: [1.0, 0, 2.3],
      roofRod: [0, ridgeY + 0.16, Z0 - 0.1],
      lpsRod: [4.3, 0, -3.6],
    };
    return { group: g, lid, lift, rooms, light, darkness, anchors: A, cut, M, L };
  };
})();
