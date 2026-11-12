// BEDAH.gedung: reusable building cross-section around a lift shaft (clay look), units: metres.
// Pit (with buffers) under the ground floor, concrete shaft walls, floor slabs reaching out into two wings
// with a little furniture, a machine room on top, and a ground-floor lobby in front of the shaft
// (landing doors, call button, floor indicator). The front of everything at z > shaft.z1 is the dollhouse
// cut: stage.setCut(G.cut) shows the shaft; stage.setCut(99) shows the lobby wall and doors.
// Options: { shaft: {x0, x1, z0, z1}, pit, floorH, floors, wing, mrH, holes: [[xa, xb], ...] (rope holes in
// the machine-room floor) }.
(function () {
  const B = window.BEDAH;

  function make(S, o = {}) {
    const { stage, THREE } = S, { add } = stage;
    const sh = Object.assign({ x0: -1.25, x1: 1.95, z0: -1.0, z1: 0.95 }, o.shaft || {});
    const t = 0.2, pit = o.pit ?? 1.4, fh = o.floorH ?? 3.3, nF = o.floors ?? 4, wing = o.wing ?? 3.0, mrH = o.mrH ?? 2.8;
    const lobbyD = o.lobbyDepth ?? 3.2;
    const levels = Array.from({ length: nF }, (_, i) => pit + i * fh);
    const mrY = pit + nF * fh, roofY = mrY + mrH;
    const XL = sh.x0 - t - wing, XR = sh.x1 + t + wing, ZB = sh.z0 - t, ZF = sh.z1 + lobbyD;
    const g = new THREE.Group(); stage.scene.add(g);
    const C = (hex, ex) => stage.toon(hex, true, ex), P = (hex, ex) => stage.toon(hex, false, ex);
    const concrete = C(0xcfc8bc), slabM = C(0xbdb5a8), plaster = C(0xeee5d6), soil = C(0x8a6a4c);
    const boxAt = (x0, x1, y0, y1, z0, z1, m, parent = g) => add(B.box(x1 - x0, y1 - y0, z1 - z0), m, parent, [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]);

    // ground: soil around the pit (open at the front cut), grass line on top
    boxAt(XL - 1.5, XR + 1.5, -0.9, -0.2, ZB - 1.5, ZF + 1.0, soil);
    boxAt(XL - 1.5, sh.x0 - t, -0.2, pit - 0.25, ZB - 1.5, ZF + 1.0, soil);
    boxAt(sh.x1 + t, XR + 1.5, -0.2, pit - 0.25, ZB - 1.5, ZF + 1.0, soil);
    boxAt(sh.x0 - t, sh.x1 + t, -0.2, pit - 0.25, ZB - 1.5, ZB, soil);
    boxAt(XL - 1.5, XR + 1.5, pit - 0.27, pit - 0.25, ZB - 1.5, ZF + 1.0, C(0xa9c98a));
    // pit floor + buffers
    boxAt(sh.x0 - t, sh.x1 + t, -0.2, 0, ZB, sh.z1 + t, concrete);
    const buffers = (o.buffers || [[0, 0], [1.45, 0]]).map(([x, z]) => {
      add(B.cyl(0.09, 0.08, 20), P(0x3c4248), g, [x, 0.04, z]);
      return add(B.coil(0.08, 0.45, 7, 0.018), P(0xd9a13a), g, [x, 0.08, z]);
    });

    // shaft walls (back + sides), up to the machine room roof
    boxAt(sh.x0 - t, sh.x1 + t, -0.2, roofY, ZB, sh.z0, concrete);
    boxAt(sh.x0 - t, sh.x0, -0.2, mrY, sh.z0, sh.z1, concrete);
    boxAt(sh.x1, sh.x1 + t, -0.2, mrY, sh.z0, sh.z1, concrete);

    // floor slabs in both wings + building back wall + windows + a little furniture per floor
    const furn = [
      (x, y, z) => { boxAt(x - 0.6, x + 0.6, y, y + 0.75, z - 0.35, z + 0.35, C(0xb98a5e)); boxAt(x - 0.2, x + 0.2, y, y + 0.45, z + 0.45, z + 0.85, C(0x5d8bc4)); },  // desk + chair
      (x, y, z) => { boxAt(x - 0.8, x + 0.8, y, y + 0.45, z - 0.4, z + 0.4, C(0x7a9a6a)); boxAt(x - 0.8, x + 0.8, y + 0.45, y + 0.85, z - 0.4, z - 0.2, C(0x7a9a6a)); },  // sofa
      (x, y, z) => { add(B.cyl(0.18, 0.4, 16), C(0xc86f4a), g, [x, y + 0.2, z]); add(new THREE.SphereGeometry(0.38, 16, 12), C(0x5f9a58), g, [x, y + 0.75, z]); },  // plant
    ];
    [...levels, mrY].forEach((y, i) => {
      [[XL, sh.x0 - t], [sh.x1 + t, XR]].forEach(([a, b], side) => {
        boxAt(a, b, y - 0.25, y, ZB, ZF, slabM);
        if (i < nF) {
          boxAt(a, b, y, y + fh - 0.25, ZB - 0.2, ZB, plaster);
          const wx = (a + b) / 2;
          add(B.box(1.4, 1.2, 0.03), P(0xbfe0f2, { roughness: 0.2 }), g, [wx, y + 1.6, ZB + 0.02]);
          add(B.box(1.5, 0.06, 0.08), P(0xffffff), g, [wx, y + 0.97, ZB + 0.05]);
          if (i > 0) furn[(i + side) % 3](wx + (side ? 0.4 : -0.4), y, ZB + 1.2);
        }
      });
      // facade columns at the wing ends
      if (i < nF) [XL, XR].forEach(x => boxAt(x - 0.15, x + 0.15, y, y + fh - 0.25, ZB, ZF, concrete));
    });
    // machine-room floor over the shaft, with rope holes
    const holes = (o.holes || [[-0.12, 0.12], [1.33, 1.57], [-1.25, -0.75]]).slice().sort((a, b) => a[0] - b[0]);
    let xa = sh.x0;
    holes.forEach(([h0, h1]) => { if (h0 > xa) boxAt(xa, h0, mrY - 0.25, mrY, sh.z0, sh.z1, slabM); xa = Math.max(xa, h1); });
    if (xa < sh.x1) boxAt(xa, sh.x1, mrY - 0.25, mrY, sh.z0, sh.z1, slabM);
    // machine room: side walls + roof + control cabinet
    boxAt(sh.x0 - t - 0.7, sh.x0 - 0.5 - t, mrY, roofY, ZB, sh.z1 + t, concrete);
    boxAt(sh.x1 + t + 0.5, sh.x1 + t + 0.7, mrY, roofY, ZB, sh.z1 + t, concrete);
    boxAt(sh.x0 - t - 0.7, sh.x1 + t + 0.7, roofY, roofY + 0.22, ZB, sh.z1 + t, slabM);
    boxAt(sh.x0 - 0.3, sh.x0 + 0.3, mrY, mrY + 1.8, sh.z0 + 0.02, sh.z0 + 0.42, C(0x8f969c));
    add(B.box(0.4, 0.3, 0.02), P(0x2f3439), g, [sh.x0, mrY + 1.3, sh.z0 + 0.43]);

    // ------------------------------------------------------------ lobby (ground floor, in front of the shaft)
    const lobby = new THREE.Group(); g.add(lobby);
    const y0 = levels[0], yTop = y0 + fh - 0.25, dw = 0.9, dh = 2.1, zf = sh.z1, wallM = P(0xe6dac6);
    boxAt(XL, -dw / 2 - 0.12, y0, yTop, zf, zf + t, wallM, lobby);
    boxAt(dw / 2 + 0.12, XR, y0, yTop, zf, zf + t, wallM, lobby);
    boxAt(-dw / 2 - 0.12, dw / 2 + 0.12, y0 + dh + 0.12, yTop, zf, zf + t, wallM, lobby);
    const steel = P(0xc9ced2, { metalness: 0.1, roughness: 0.3 });
    boxAt(-dw / 2 - 0.12, -dw / 2, y0, y0 + dh + 0.12, zf + t - 0.02, zf + t + 0.03, steel, lobby);     // architrave
    boxAt(dw / 2, dw / 2 + 0.12, y0, y0 + dh + 0.12, zf + t - 0.02, zf + t + 0.03, steel, lobby);
    boxAt(-dw / 2 - 0.12, dw / 2 + 0.12, y0 + dh, y0 + dh + 0.12, zf + t - 0.02, zf + t + 0.03, steel, lobby);
    boxAt(-dw / 2 - 0.12, dw / 2 + 0.12, y0, y0 + 0.02, zf, zf + t + 0.06, P(0x9aa1a7), lobby);        // sill
    const doorM = P(0xd5dadd, { metalness: 0.1, roughness: 0.28 });
    const doors = [-1, 1].map(s => { const d = add(B.box(dw / 2, dh, 0.03), doorM, lobby, [s * dw / 4, y0 + dh / 2, zf + t / 2]); d.userData = { x0: s * dw / 4, s }; return d; });
    add(B.box(0.004, dh, 0.032), P(0x8f969c), lobby, [0, y0 + dh / 2, zf + t / 2]);
    // call button panel
    add(B.box(0.1, 0.24, 0.015), steel, lobby, [dw / 2 + 0.32, y0 + 1.05, zf + t + 0.01]);
    const ringM = P(0xffffff, { emissive: 0xffc94a, emissiveIntensity: 0 });
    const btns = [0.05, -0.05].map(dy => { add(B.cyl(0.024, 0.012, 20), ringM, lobby, [dw / 2 + 0.32, y0 + 1.05 + dy, zf + t + 0.02], [Math.PI / 2, 0, 0]);
      return add(B.cyl(0.016, 0.016, 20), P(0xe8ebee, { metalness: 0.1 }), lobby, [dw / 2 + 0.32, y0 + 1.05 + dy, zf + t + 0.024], [Math.PI / 2, 0, 0]); });
    // floor indicator above the door
    const indC = document.createElement('canvas'); indC.width = 128; indC.height = 48;
    const indT = new THREE.CanvasTexture(indC);
    const drawInd = (txt, arrow) => { const c = indC.getContext('2d'); c.fillStyle = '#15181b'; c.fillRect(0, 0, 128, 48);
      c.fillStyle = '#ff6a3d'; c.font = '800 34px "JetBrains Mono", monospace'; c.textAlign = 'center'; c.fillText(txt, 78, 37);
      if (arrow) { c.beginPath(); const up = arrow > 0; c.moveTo(22, up ? 12 : 36); c.lineTo(34, up ? 30 : 18); c.lineTo(10, up ? 30 : 18); c.closePath(); c.fill(); }
      indT.needsUpdate = true; };
    drawInd('G', 0);
    add(B.box(0.36, 0.14, 0.02), P(0x15181b), lobby, [0, y0 + dh + 0.32, zf + t + 0.01]);
    add(new THREE.PlaneGeometry(0.32, 0.12), P(0xffffff, { map: indT, emissive: 0xffffff, emissiveMap: indT, emissiveIntensity: 0.6 }), lobby, [0, y0 + dh + 0.32, zf + t + 0.022]);
    // lobby floor finish + a plant + a bench
    add(B.box(XR - XL, 0.01, lobbyD - t), P(0xe9e3d8, { roughness: 0.25 }), lobby, [(XL + XR) / 2, y0 + 0.006, zf + t + (lobbyD - t) / 2]);
    add(B.cyl(0.2, 0.45, 18), P(0xc86f4a), lobby, [-1.9, y0 + 0.225, zf + 0.7]);
    add(new THREE.SphereGeometry(0.42, 16, 12), P(0x5f9a58), lobby, [-1.9, y0 + 0.85, zf + 0.7]);
    add(B.box(1.2, 0.08, 0.4), P(0xb98a5e), lobby, [2.1, y0 + 0.45, zf + 0.6]);
    [-0.5, 0.5].forEach(dx => add(B.box(0.06, 0.45, 0.35), P(0x3c4248), lobby, [2.1 + dx, y0 + 0.225, zf + 0.6]));

    return {
      group: g, lobby, levels, mrY, roofY, pit, shaft: sh, cut: sh.z1 + 0.002, buffers,
      setDoors(k) { doors.forEach(d => { d.position.x = d.userData.x0 + d.userData.s * k * dw / 2 * 0.98; }); },
      setCall(k) { ringM.emissiveIntensity = 1.6 * k; ringM.color.set(k > 0.5 ? 0xffe08a : 0xffffff); },
      setIndicator: drawInd,
    };
  }
  B.gedung = (S, o) => make(S, o);
})();
