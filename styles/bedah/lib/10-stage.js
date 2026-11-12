// BEDAH: flat toon 3D cutaway stage (Three.js r149, global THREE) for 1080x1920 "kok bisa?" shorts.
// Shared by every bedah video; a project only writes model.js (see styles/bedah/guide.md).
// Everything here is a pure function of t: no requestAnimationFrame, no clock, no unseeded random.
(function () {
  const W = 1080, H = 1920;

  // name -> [hex, clipped]. Clipped materials are cut by the cutaway and draw both faces,
  // so the inside of a shell shows once it is opened. Moving internals use solid ones.
  const PALETTE = {
    shell: [0xeceef1, true], shellSolid: [0xeceef1, false],   // white/light-grey plastic body
    grey: [0xb9bdc4, true], greySolid: [0xb9bdc4, false],     // metal, inner pot
    steel: [0x9aa1ab, false], steelClip: [0x9aa1ab, true],
    dark: [0x3a3d45, false], darkClip: [0x3a3d45, true],      // rubber, belts, burners
    ink: [0x23252b, false],
    copper: [0xd9804f, true], copperSolid: [0xd9804f, false], // heating plates, coils
    brass: [0xc9962f, true], brassSolid: [0xc9962f, false],
    yellow: [0xf3c843, false],                                // the highlight colour, solid
    blue: [0x3b6fe0, false], blueClip: [0x3b6fe0, true],      // magnets, water-side parts
    red: [0xe0393e, false], redClip: [0xe0393e, true], brick: [0xd24b3e, true],
    green: [0x2f8f5b, false],                                 // circuit boards
    orange: [0xef8a3a, false],
    cream: [0xf5efe2, false],
    wood: [0xd9b98c, false],
    floor: [0xe4e2dd, false], wall: [0xefeeea, false],
  };
  const HL = new THREE.Color(0xf3c843);   // highlight yellow (the part the narrator talks about)
  const GROUND = 0xf7f7f5;

  function createStage(opts = {}) {
    const canvas = document.getElementById('gl');
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(1);
    renderer.setSize(W, H, false);
    renderer.setClearColor(opts.ground ?? GROUND, 1);
    renderer.localClippingEnabled = true;
    // look: 'toon' (default: flat 3-step shading + ink outlines) | 'clay' (soft, toy-like, shadows, no outlines)
    const clay = opts.look === 'clay';
    if (clay) { renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap; }

    const scene = new THREE.Scene();
    const fh = opts.frustumH || 10;
    const camera = new THREE.OrthographicCamera(-fh * W / H / 2, fh * W / H / 2, fh / 2, -fh / 2, 0.1, 200);
    let camDir = new THREE.Vector3(...(opts.camDir || [1.0, 0.85, 1.25])).normalize();

    const hemi = clay ? new THREE.HemisphereLight(0xfff6e8, 0xc4b39a, 0.95) : new THREE.HemisphereLight(0xffffff, 0xa8a49c, 0.62);
    const sun = new THREE.DirectionalLight(clay ? 0xfff0da : 0xffffff, clay ? 0.8 : 0.62);
    sun.position.set(4, 9, 6);
    scene.add(hemi, sun);
    if (clay) {
      const r = opts.shadowSize ?? 10;
      Object.assign(sun.shadow.camera, { left: -r, right: r, top: r, bottom: -r, near: 0.5, far: 40 });
      sun.shadow.mapSize.set(opts.shadowMap ?? 1024, opts.shadowMap ?? 1024);
      sun.shadow.bias = -0.0006; sun.shadow.radius = 5; sun.castShadow = true;
      scene.add(sun.target);
    }
    const lightBase = [hemi.intensity, sun.intensity];
    // setDim(k): 1 = normal, 0.3 = the house is dark (power cut)
    function setDim(k) { hemi.intensity = lightBase[0] * k; sun.intensity = lightBase[1] * k; }
    // setSky(color): background colour (storms, night)
    function setSky(c) { renderer.setClearColor(c, 1); }

    // 3-step toon ramp from an RGBA canvas (a RedFormat DataTexture fails on some GPUs).
    const rc = document.createElement('canvas'); rc.width = 3; rc.height = 1;
    const rx = rc.getContext('2d');
    [150, 205, 245].forEach((v, i) => { rx.fillStyle = `rgb(${v},${v},${v})`; rx.fillRect(i, 0, 1, 1); });
    const ramp = new THREE.CanvasTexture(rc);
    ramp.minFilter = ramp.magFilter = THREE.NearestFilter; ramp.generateMipmaps = false;

    // Cutaway. 'plane': keeps z <= c. 'wedge': removes the quarter where z > c AND x > c
    // (the classic cut-open corner). Animate with setCut(c): 3 = closed, 0 = open to the axis.
    const cutMode = opts.cut || 'wedge';
    const cutZ = new THREE.Plane(new THREE.Vector3(0, 0, -1), 50);
    const cutX = new THREE.Plane(new THREE.Vector3(-1, 0, 0), 50);
    const planes = cutMode === 'wedge' ? [cutZ, cutX] : [cutZ];
    const cutOrigin = new THREE.Vector3(...(opts.cutOrigin || [0, 0, 0]));
    function setCut(c) {
      cutZ.constant = cutOrigin.z + c;
      cutX.constant = cutOrigin.x + c;
    }

    function toon(color, clipped, extra = {}) {
      if (clay) return new THREE.MeshStandardMaterial(Object.assign({
        color, roughness: 0.82, metalness: 0, side: THREE.FrontSide,
        clippingPlanes: clipped ? planes : [], clipIntersection: cutMode === 'wedge',
      }, extra));
      return new THREE.MeshToonMaterial(Object.assign({
        color, gradientMap: ramp,
        side: THREE.FrontSide,
        clippingPlanes: clipped ? planes : [],
        clipIntersection: cutMode === 'wedge',
      }, extra));
    }
    // Material.clone() copies the clipping planes (frozen at their current position); re-link them so a
    // cloned material keeps following the animated cut. Use this for every clone of a stage material.
    function cloneMat(mat) { const m = mat.clone(); m.clippingPlanes = mat.clippingPlanes; return m; }
    // inside of a cut shell: same colour, darker, drawn on the back faces -> the cut reads at a glance
    const insideCache = new Map();
    function insideOf(mat) {
      if (!insideCache.has(mat)) {
        const m = cloneMat(mat); m.side = THREE.BackSide; m.color = mat.color.clone().multiplyScalar(0.72);
        insideCache.set(mat, m);
      }
      return insideCache.get(mat);
    }
    // silhouette outline: inverted hull pushed out along the normals, drawn on back faces in ink
    const hullCache = new Map();
    function hullOf(mat) {
      const clip = !!(mat.clippingPlanes && mat.clippingPlanes.length);
      if (!hullCache.has(clip)) {
        const m = new THREE.MeshBasicMaterial({ color: 0x2b2b2b, side: THREE.BackSide,
          clippingPlanes: clip ? planes : [], clipIntersection: cutMode === 'wedge' });
        m.onBeforeCompile = sh => { sh.vertexShader = sh.vertexShader.replace('#include <begin_vertex>',
          '#include <begin_vertex>\n transformed += normalize(normal) * ' + (opts.outline ?? 0.018).toFixed(4) + ';'); };
        hullCache.set(clip, m);
      }
      return hullCache.get(clip);
    }
    const edgeMat = new THREE.LineBasicMaterial({ color: 0x2b2b2b, transparent: true, opacity: 0.55 });
    const edgeMatClip = edgeMat.clone();
    edgeMatClip.clippingPlanes = planes; edgeMatClip.clipIntersection = cutMode === 'wedge';

    // add(geometry, material, parent, [x,y,z], [rx,ry,rz], edges=true) -> mesh with ink outline
    function add(geo, mat, parent, pos, rot, edges = true) {
      const m = new THREE.Mesh(geo, mat);
      if (pos) m.position.set(pos[0], pos[1], pos[2]);
      if (rot) m.rotation.set(rot[0], rot[1], rot[2]);
      const clipped = !!(mat.clippingPlanes && mat.clippingPlanes.length);
      if (clipped && !mat.transparent) m.add(Object.assign(new THREE.Mesh(geo, insideOf(mat)), { userData: { inside: true } }));
      if (clay) {  // soft shadows instead of ink lines
        if (!mat.transparent) { m.castShadow = true; m.receiveShadow = true; m.children.forEach(c => { c.receiveShadow = true; }); }
      } else if (edges) {
        m.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo, 30), clipped ? edgeMatClip : edgeMat));
        if (!mat.transparent) m.add(Object.assign(new THREE.Mesh(geo, hullOf(mat)), { userData: { hull: true } }));
      }
      (parent || scene).add(m);
      return m;
    }

    const C = {};
    Object.entries(Object.assign({}, PALETTE, opts.palette)).forEach(([k, [hex, clip]]) => { C[k] = toon(hex, clip); });
    // see-through glass / water: transparent, no outline needed
    C.glass = toon(0xd8ecf5, true, { transparent: true, opacity: 0.35, depthWrite: false });
    C.water = toon(0x8cc8f0, true, { transparent: true, opacity: 0.55, depthWrite: false });

    function room(o = {}) {
      if (o.floor !== false) add(new THREE.BoxGeometry(16, 0.2, 9), C.floor, null, [0, (o.y ?? -0.35), 0.6]);
      if (o.wall) add(new THREE.BoxGeometry(16, 8, 0.2), C.wall, null, [0, 3.6, -3.4]);
      const sh = new THREE.Mesh(new THREE.CircleGeometry(o.shadowRadius || 1.3, 40),
        new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.08 }));
      sh.rotation.x = -Math.PI / 2;
      sh.scale.set(...(o.shadowScale || [1.5, 1, 1]));
      sh.position.set(...(o.shadowAt || [0, (o.y ?? -0.35) + 0.11, 0]));
      scene.add(sh);
      return sh;
    }

    // Cut faces of a turned wall: the region between two lathe profiles [[r, y], ...] (outer, inner),
    // drawn flat and outlined on the cutaway faces so a cut wall looks solid, like a technical drawing.
    // A profile that reaches r = 0 (a stopper, a knob) can pass inner = [] for a solid section.
    // Shown only while the cut is open (setCut <= 0.05). Parent must have its axis at x = z = 0.
    const sections = [];
    let cutNow = 50;
    function section(outer, inner, mat, parent, o = {}) {
      const geo = new THREE.ShapeGeometry(polyShape(outer.concat(inner.slice().reverse())));
      const m = mat.clone();
      m.side = THREE.DoubleSide; m.clippingPlanes = []; m.transparent = false; m.opacity = 1; m.depthWrite = true;
      m.color = mat.color.clone().multiplyScalar(o.shade ?? 0.9);
      const g = new THREE.Group(); (parent || scene).add(g);
      const faces = cutMode === 'wedge'
        ? [[[0, 0, 0.004], 0, 1], [[0.004, 0, 0], -Math.PI / 2, 1]]
        : [[[0, 0, 0.004], 0, 1], [[0, 0, 0.004], 0, -1]];
      faces.forEach(([p, ry, sx]) => {
        const f = new THREE.Mesh(geo, m);
        f.position.set(...p); f.rotation.y = ry; f.scale.x = sx;
        if (!clay) f.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo, 20), edgeMat));
        g.add(f);
      });
      g.visible = cutNow <= 0.05;
      sections.push(g);
      return g;
    }
    const _setCut = setCut;
    function setCutAll(c) { cutNow = c; _setCut(c); sections.forEach(g => { g.visible = c <= 0.05; }); }

    // Camera: fixed isometric-style direction; a shot = target point + zoom (+ optional orbit yaw,
    // pitch 0..1 toward straight top-down, shake [dx, dy] in world units along the screen axes).
    function setCamera(target, zoom, yaw = 0, pitch = 0, shake = null) {
      const tgt = new THREE.Vector3().fromArray(target);
      let d = camDir.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
      const pk = Math.min(Math.max(pitch, 0), 1);
      if (pk > 0) d = d.lerp(new THREE.Vector3(0.0001, 1, 0.02), pk).normalize();
      if (pitch < 0) {   // negative pitch: lower the camera toward eye level (look in under a ceiling)
        const flat = new THREE.Vector3(d.x, 0, d.z).normalize(); flat.y = 0.06;
        d = d.lerp(flat.normalize(), Math.min(-pitch, 1)).normalize();
      }
      camera.position.copy(tgt).addScaledVector(d, 60);
      camera.up.set(0, 1 - pk * 0.98, -pk).normalize();
      camera.lookAt(tgt);
      if (shake) {
        camera.updateMatrixWorld();
        const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0), up = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
        camera.position.addScaledVector(right, shake[0]).addScaledVector(up, shake[1]);
      }
      camera.zoom = zoom;
      camera.updateProjectionMatrix();
    }

    const tmp = new THREE.Vector3();
    function toScreen(obj, p) {
      if (p) tmp.fromArray(p); else tmp.set(0, 0, 0);
      obj.localToWorld(tmp).project(camera);
      return [(tmp.x + 1) / 2 * W, (1 - tmp.y) / 2 * H];
    }

    // Transparent cable along points, with glowing particles flowing inside:
    //   const c = stage.cable([[x,y,z], ...], { r, parent, color });  c.flow(t, { speed, on, color, reach })
    // speed ~ particle speed (negative = backwards), on = 0..1 (particles shrink away at 0),
    // reach = 0..1 how far along the cable the particles get. c.grow(k) draws only the first k of it.
    const flowMat = new THREE.MeshBasicMaterial({ color: 0xffd23f });
    function cable(points, o = {}) {
      const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p)), false, 'catmullrom', 0.1);
      const len = curve.getLength();
      const r = o.r ?? 0.045;
      const seg = Math.max(24, Math.round(len * 24));
      const geo = new THREE.TubeGeometry(curve, seg, r, 10, false);
      const mat = toon(o.color ?? 0xf6f1e6, !!o.clip, { transparent: true, opacity: o.opacity ?? 0.42, depthWrite: false });
      const mesh = new THREE.Mesh(geo, mat); (o.parent || scene).add(mesh);
      const coreGeo = new THREE.TubeGeometry(curve, seg, r * 0.28, 6, false);
      const core = new THREE.Mesh(coreGeo, toon(o.core ?? 0xb87333, !!o.clip)); (o.parent || scene).add(core);
      const n = o.n ?? Math.max(4, Math.round(len * 3.5));
      const pm = flowMat.clone(); if (o.particleColor !== undefined) pm.color.set(o.particleColor);
      const parts = [];
      for (let i = 0; i < n; i++) { const sp = new THREE.Mesh(new THREE.SphereGeometry(r * 0.62, 10, 8), pm); sp.renderOrder = 2; (o.parent || scene).add(sp); parts.push(sp); }
      const tmpV = new THREE.Vector3();
      return {
        curve, mesh, core, parts, mat, pm, len,
        grow(k) {
          k = Math.max(0, Math.min(1, k));
          geo.setDrawRange(0, Math.round(geo.index.count * k / 6) * 6);
          coreGeo.setDrawRange(0, Math.round(coreGeo.index.count * k / 6) * 6);
          mesh.visible = core.visible = k > 0;
        },
        flow(t, f = {}) {
          const on = f.on ?? 1, sp = (f.speed ?? 1) / Math.max(len, 0.5), reach = f.reach ?? 1;
          if (f.color !== undefined) pm.color.set(f.color);
          parts.forEach((m, i) => {
            const u = (((t * sp + i / n) % 1) + 1) % 1;
            m.visible = on > 0.01 && u <= reach;
            if (!m.visible) return;
            curve.getPointAt(Math.min(u, 0.9999), tmpV); m.position.copy(tmpV);
            m.scale.setScalar(on * (0.8 + 0.2 * Math.sin(t * 9 + i * 1.7)));
          });
        },
      };
    }

    return { W, H, renderer, scene, camera, C, toon, cloneMat, add, room, setCamera, setCut: setCutAll, section, toScreen, planes,
      setDim, setSky, cable, clay, sun, hemi,
      render: () => renderer.render(scene, camera) };
  }

  // ---------- geometry helpers ----------
  const cyl = (r, h, seg = 48, open = false) => new THREE.CylinderGeometry(r, r, h, seg, 1, open);
  const tube = (r, h, seg = 48) => new THREE.CylinderGeometry(r, r, h, seg, 1, true);  // open: you can see in
  const box = (w, h, d) => new THREE.BoxGeometry(w, h, d);
  const ALONG_X = [0, 0, Math.PI / 2], ALONG_Z = [Math.PI / 2, 0, 0];
  // lathe([[r, y], ...]) — a turned profile (pots, bottles, knobs, nozzles)
  const lathe = (pts, seg = 64) => new THREE.LatheGeometry(pts.map(([r, y]) => new THREE.Vector2(r, y)), seg);
  // rounded box (bodies of devices)
  function rbox(w, h, d, r = 0.08, depthSeg = 1, bevel = 0) {
    const s = new THREE.Shape(), x = -w / 2, y = -h / 2;
    s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r);
    s.lineTo(x + w, y + h - r); s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r);
    s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y);
    const g = new THREE.ExtrudeGeometry(s, bevel > 0
      ? { depth: Math.max(d - 2 * bevel, 0.001), bevelEnabled: true, bevelThickness: bevel, bevelSize: bevel * 0.9, bevelSegments: 3, steps: depthSeg, curveSegments: 6 }
      : { depth: d, bevelEnabled: false, steps: depthSeg, curveSegments: 6 });
    g.translate(0, 0, bevel > 0 ? -(d - 2 * bevel) / 2 : -d / 2);
    return g;
  }
  function gearGeo(r, teeth, toothDepth, depth = 0.05) {
    const s = new THREE.Shape(), n = teeth * 4;
    for (let i = 0; i <= n; i++) {
      const a = i / n * Math.PI * 2, rad = i % 4 < 2 ? r : r - toothDepth;
      i ? s.lineTo(Math.cos(a) * rad, Math.sin(a) * rad) : s.moveTo(Math.cos(a) * rad, Math.sin(a) * rad);
    }
    const g = new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: false });
    g.rotateX(-Math.PI / 2);
    return g;
  }
  function polyShape(points) { const s = new THREE.Shape(); points.forEach(([x, y], i) => i ? s.lineTo(x, y) : s.moveTo(x, y)); return s; }
  // helix spring / coil along y
  function coil(r, h, turns, wire = 0.025) {
    const pts = []; const n = Math.ceil(turns * 32);
    for (let i = 0; i <= n; i++) { const a = i / n * turns * Math.PI * 2; pts.push(new THREE.Vector3(Math.cos(a) * r, i / n * h - h / 2, Math.sin(a) * r)); }
    return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), n, wire, 8, false);
  }

  // ---------- time ----------
  const smooth = x => x * x * (3 - 2 * x);
  const clamp01 = x => Math.max(0, Math.min(1, x));
  // keys [[t, value|array], ...], smoothstep between keys
  function kf(t, keys) {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      const [t1, v1] = keys[i], [t0, v0] = keys[i - 1];
      if (t <= t1) { const u = smooth((t - t0) / Math.max(t1 - t0, 1e-6));
        return Array.isArray(v0) ? v0.map((v, k) => v + (v1[k] - v) * u) : v0 + (v1 - v0) * u; }
    }
    return keys[keys.length - 1][1];
  }
  // integral of a rate curve (rev/s, L/s ...) from 0 to t
  function integrate(t, rateKeys, step = 1 / 120) {
    let s = 0; for (let x = 0; x < t; x += step) s += kf(Math.min(x + step / 2, t), rateKeys) * Math.min(step, t - x); return s;
  }
  function wheelPos(value, place) {
    const q = value / place; if (place === 1) return q % 10;
    return (Math.floor(q) % 10) + Math.max(0, ((value % place) / place - 0.9) * 10);
  }
  const hash = n => { const v = Math.sin(n * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };

  window.BEDAH = Object.assign(window.BEDAH || {}, {
    W, H, PALETTE, HL, createStage, cyl, tube, box, lathe, rbox, gearGeo, polyShape, coil, ALONG_X, ALONG_Z,
    smooth, clamp01, kf, integrate, wheelPos, hash,
    // model.js: BEDAH.film(S => { build; return { frame(t, si), readout(t), spark } })
    film(fn) { window.BEDAH._film = fn; },
  });
})();
