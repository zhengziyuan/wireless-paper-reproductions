/* MIS digital twin — offline Three.js r158 renderer.
   Display coordinates use one cell pitch as one unit. Layer gap is visually
   exaggerated. Beam radius is an explicit absolute -35…0 dB display mapping,
   not electromagnetic propagation distance. */
(function () {
  'use strict';
  const T = window.THREE;
  const TAU = 2 * Math.PI;
  const clamp = (x, lo, hi) => Math.min(hi, Math.max(lo, x));
  const phaseColor = (phase) => new T.Color().setHSL(((phase / TAU) % 1 + 1) % 1, .86, .58);
  const beamColor = (power) => {
    const dB = 10 * Math.log10(Math.max(1e-12, power));
    const v = clamp((dB + 35) / 35, 0, 1);
    const c = new T.Color();
    if (v < .5) c.setRGB(.13 + .05 * v, .30 + 1.1 * v, .78 + .18 * v);
    else if (v < .82) c.setRGB(.15 + 2.35 * (v - .5), .85, .80 - 2.3 * (v - .5));
    else c.setRGB(.92 + .4 * (v - .82), .85 - 2.4 * (v - .82), .065);
    return c;
  };

  window.createMISScene = function createMISScene(container) {
    if (!T) throw new Error('Three.js 尚未加载。请保留 vendor/three.min.js。');
    const scene = new T.Scene();
    scene.background = new T.Color('#08131f');
    scene.fog = new T.FogExp2('#08131f', .009);
    const renderer = new T.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
    renderer.outputColorSpace = T.SRGBColorSpace;
    renderer.toneMapping = T.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.23;
    renderer.domElement.style.cssText = 'display:block;width:100%;height:100%;touch-action:none;cursor:grab;';
    renderer.domElement.setAttribute('aria-label', '可拖动旋转、滚轮缩放的双层 MIS 三维数字孪生');
    container.appendChild(renderer.domElement);
    const camera = new T.PerspectiveCamera(43, 1, .1, 180);
    const target = new T.Vector3(0, 0, 5);
    const orbit = { radius: 39, theta: -.80, phi: 1.02 };
    let disposed = false, animation, size = { w: 0, h: 0 };
    let drag = null, prevTime = 0, lastBeam = null;
    const params = { shiftX: 0, shiftY: 0, gap: 4, showBeam: true, showWaves: false, showPhases: true,
      phi1: [], phi2: [], receiver: { ux: 0, uy: 0, uz: 1 }, layerVisible: true };
    const smooth = { x: 0, y: 0, gap: 4 };
    const materials = [];
    const addMaterial = m => { materials.push(m); return m; };
    scene.add(new T.HemisphereLight(0xbbe5ff, 0x061321, 2.4));
    const keyLight = new T.DirectionalLight(0xf2f8ff, 3.3);
    keyLight.position.set(6, -11, 25); scene.add(keyLight);
    const fillLight = new T.DirectionalLight(0x339ee5, 2.0);
    fillLight.position.set(-10, 10, -3); scene.add(fillLight);

    function line(points, color, opacity = 1, dashed = false) {
      const geo = new T.BufferGeometry().setFromPoints(points.map(p => new T.Vector3(...p)));
      const mat = addMaterial(dashed ? new T.LineDashedMaterial({ color, transparent: true, opacity, dashSize: .25, gapSize: .20 })
        : new T.LineBasicMaterial({ color, transparent: true, opacity }));
      const obj = new T.Line(geo, mat);
      if (dashed) obj.computeLineDistances();
      return obj;
    }
    function rectangle(w, h, z, color, opacity = 1) {
      return line([[-w/2,-h/2,z], [w/2,-h/2,z], [w/2,h/2,z], [-w/2,h/2,z], [-w/2,-h/2,z]], color, opacity);
    }
    function label(text, color = '#a8cfe9', scale = 3.4) {
      const canvas = document.createElement('canvas'); canvas.width = 512; canvas.height = 112;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = 'rgba(6,18,30,0.83)'; ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(4, 8, 504, 96, 18); else ctx.rect(4, 8, 504, 96);
      ctx.fill(); ctx.strokeStyle = color; ctx.globalAlpha = .28; ctx.lineWidth = 2; ctx.stroke(); ctx.globalAlpha = 1;
      ctx.font = '500 52px "Microsoft YaHei", "Segoe UI", sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillStyle = color; ctx.fillText(text, 256, 57);
      const tex = new T.CanvasTexture(canvas); tex.colorSpace = T.SRGBColorSpace;
      const mat = addMaterial(new T.SpriteMaterial({ map: tex, transparent: true, depthTest: false, opacity: .96 }));
      const obj = new T.Sprite(mat); obj.scale.set(scale, scale * 112 / 512, 1); obj.renderOrder = 10;
      return obj;
    }
    function bar(w, h, d, x, y, z, color = 0x314b60) {
      const mesh = new T.Mesh(new T.BoxGeometry(w, h, d), addMaterial(new T.MeshStandardMaterial({ color, metalness: .68, roughness: .35 })));
      mesh.position.set(x, y, z); return mesh;
    }
    function layer(n, title, accent) {
      const group = new T.Group();
      const plate = new T.Mesh(new T.BoxGeometry(n + .18, n + .18, .09), addMaterial(new T.MeshStandardMaterial({ color: 0x071821, metalness: .3, roughness: .7 })));
      plate.position.z = -.085; group.add(plate);
      const material = addMaterial(new T.MeshStandardMaterial({ roughness: .55, metalness: .2, emissive: 0x091a20, emissiveIntensity: .9 }));
      const cells = new T.InstancedMesh(new T.BoxGeometry(.91, .91, .08), material, n * n);
      const dummy = new T.Object3D();
      for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
        dummy.position.set(j - (n - 1) / 2, i - (n - 1) / 2, 0); dummy.updateMatrix();
        cells.setMatrixAt(i * n + j, dummy.matrix); cells.setColorAt(i * n + j, phaseColor(0));
      }
      cells.instanceMatrix.needsUpdate = true; cells.instanceColor.needsUpdate = true; group.add(cells);
      for (const s of [-1, 1]) {
        group.add(bar(n + .55, .22, .3, 0, s * (n / 2 + .22), -.06));
        group.add(bar(.22, n + .55, .3, s * (n / 2 + .22), 0, -.06));
      }
      group.add(rectangle(n + .36, n + .36, .13, accent, .95));
      for (const x of [-1, 1]) for (const y of [-1, 1]) {
        const bolt = new T.Mesh(new T.CylinderGeometry(.075, .075, .055, 8), addMaterial(new T.MeshStandardMaterial({ color: 0xa4bece, metalness: .8, roughness: .22 })));
        bolt.rotation.x = Math.PI / 2; bolt.position.set(x * (n / 2 + .22), y * (n / 2 + .22), .13); group.add(bolt);
      }
      const name = label(title, accent === 0x49d5eb ? '#70e2ee' : '#e9bd78', 7.5);
      name.position.set(n === 16 ? -8 : 7, n === 16 ? -7.5 : 6.8, .8); group.add(name);
      scene.add(group);
      return { group, cells, n, name };
    }
    const first = layer(16, 'MS 1 · 固定层', 0x49d5eb);
    const second = layer(12, 'MS 2 · 移动层', 0xeab96d);
    second.group.position.z = smooth.gap;

    const rig = new T.Group(); scene.add(rig);
    for (let y = -10; y <= 10; y += 2) rig.add(line([[-10, y, -.55], [10, y, -.55]], 0x426883, .10));
    for (let x = -10; x <= 10; x += 2) rig.add(line([[x, -10, -.55], [x, 10, -.55]], 0x426883, .10));
    const rails = new T.Group(); scene.add(rails);
    for (const s of [-1, 1]) {
      rails.add(bar(20, .16, .18, 0, s * 8.95, 0, 0x375364));
      rails.add(bar(.16, 18.0, .18, s * 9.9, 0, 0, 0x375364));
      rails.add(line([[-9.7, s * 8.95, .12], [9.7, s * 8.95, .12]], 0x53bfd7, .45));
    }
    const extent = rectangle(16, 16, .01, 0xddb36b, .23); rails.add(extent);
    const axisOrigin = new T.Vector3(-10, -10, -.4);
    function axis(vector, color, title) {
      const arrow = new T.ArrowHelper(new T.Vector3(...vector), axisOrigin, 3.1, color, .45, .2); scene.add(arrow);
      const l = label(title, '#' + color.toString(16).padStart(6, '0'), 1.25);
      l.position.copy(axisOrigin).addScaledVector(new T.Vector3(...vector), 3.75); scene.add(l);
    }
    axis([1,0,0], 0xf68f88, 'X'); axis([0,1,0], 0x83d8b8, 'Y'); axis([0,0,1], 0x70bbf6, '+Z');

    const beamGroup = new T.Group(); scene.add(beamGroup);
    let beamMesh = null, beamWire = null;
    const rayGroup = new T.Group(); scene.add(rayGroup);
    const receiverRay = line([[0,0,0], [0,0,15]], 0xe9f6ff, .62, true); rayGroup.add(receiverRay);
    const receiverMarker = new T.Mesh(new T.IcosahedronGeometry(.25, 1), addMaterial(new T.MeshBasicMaterial({ color: 0xffffff })));
    rayGroup.add(receiverMarker);
    const receiverHalo = new T.Mesh(new T.SphereGeometry(.47, 16, 12), addMaterial(new T.MeshBasicMaterial({ color: 0x8ee7ff, transparent: true, opacity: .12, depthWrite: false })));
    rayGroup.add(receiverHalo);
    const receiverLabel = label('目标接收方向', '#cfedf6', 6.4); rayGroup.add(receiverLabel);
    const peakArrow = new T.ArrowHelper(new T.Vector3(0,0,1), new T.Vector3(), 13, 0x59d7c6, .65, .25);
    peakArrow.line.material.transparent = true; peakArrow.line.material.opacity = .65; beamGroup.add(peakArrow);

    const waveGroup = new T.Group(); scene.add(waveGroup);
    const incomingWaves = [];
    for (let k = 0; k < 4; k++) {
      const wave = rectangle(14.7, 14.7, 0, 0x7bcde8, .12); waveGroup.add(wave); incomingWaves.push(wave);
    }
    const sourceArrow = new T.ArrowHelper(new T.Vector3(0,0,1), new T.Vector3(0,0,-6.5), 4.5, 0x7dc7e6, .5, .23);
    waveGroup.add(sourceArrow);
    const inputLabel = label('入射平面波', '#78b3cd', 3.1); inputLabel.position.set(0,0,-6.9); waveGroup.add(inputLabel);

    function repaint(layerObj, values) {
      for (let i = 0; i < layerObj.n * layerObj.n; i++) layerObj.cells.setColorAt(i,
        params.showPhases ? phaseColor(Number(values[i] || 0)) : new T.Color(layerObj.n === 16 ? 0x218eac : 0xbb9159));
      layerObj.cells.instanceColor.needsUpdate = true;
    }
    function dropMesh(obj) { if (!obj) return; beamGroup.remove(obj); obj.geometry.dispose(); obj.material.dispose(); }
    function setBeam(beam) {
      if (!beam || !Array.isArray(beam.vertices) || !beam.rows || !beam.cols) return;
      if (beam.vertices.length !== beam.rows * beam.cols) return;
      lastBeam = beam;
      const positions = [], colors = [], indices = [], wirePositions = [];
      let maxPower = -1, maxDirection = new T.Vector3(0, 0, 1), maxRadius = 2;
      beam.vertices.forEach(p => {
        const pw = Math.max(0, Number(p.power) || 0);
        const db = 10 * Math.log10(Math.max(pw, 1e-12));
        const radius = 2 + 11 * clamp((db + 35) / 35, 0, 1);
        const dir = new T.Vector3(p.ux, p.uy, p.uz).normalize();
        positions.push(dir.x * radius, dir.y * radius, dir.z * radius);
        const col = beamColor(pw); colors.push(col.r, col.g, col.b);
        if (pw > maxPower) { maxPower = pw; maxDirection = dir; maxRadius = radius; }
      });
      for (let r = 0; r < beam.rows - 1; r++) for (let c = 0; c < beam.cols - 1; c++) {
        const a = r * beam.cols + c, b = a + 1, d = a + beam.cols, e = d + 1;
        indices.push(a, d, b, b, d, e);
      }
      for (let r = 0; r < beam.rows; r++) for (let c = 0; c < beam.cols; c++) {
        const a = (r * beam.cols + c) * 3;
        if (r % 4 === 0 && c < beam.cols - 1) wirePositions.push(...positions.slice(a, a + 3), ...positions.slice(a + 3, a + 6));
        if (c % 6 === 0 && r < beam.rows - 1) { const b = a + beam.cols * 3; wirePositions.push(...positions.slice(a, a + 3), ...positions.slice(b, b + 3)); }
      }
      const geo = new T.BufferGeometry(); geo.setAttribute('position', new T.Float32BufferAttribute(positions, 3));
      geo.setAttribute('color', new T.Float32BufferAttribute(colors, 3)); geo.setIndex(indices); geo.computeVertexNormals();
      dropMesh(beamMesh);
      beamMesh = new T.Mesh(geo, new T.MeshBasicMaterial({ vertexColors: true, side: T.DoubleSide, transparent: true, opacity: .69, depthWrite: false }));
      beamMesh.renderOrder = 2; beamGroup.add(beamMesh);
      dropMesh(beamWire);
      const wireGeo = new T.BufferGeometry(); wireGeo.setAttribute('position', new T.Float32BufferAttribute(wirePositions, 3));
      beamWire = new T.LineSegments(wireGeo, new T.LineBasicMaterial({ color: 0xc3edf3, transparent: true, opacity: .11, depthWrite: false }));
      beamWire.renderOrder = 3; beamGroup.add(beamWire);
      peakArrow.setDirection(maxDirection); peakArrow.setLength(maxRadius + .7, .5, .2);
    }
    function update(next) {
      if (!next || disposed) return;
      const recolor = next.phi1 !== undefined || next.phi2 !== undefined || next.showPhases !== undefined;
      Object.assign(params, next);
      params.shiftX = Number(params.shiftX) || 0; params.shiftY = Number(params.shiftY) || 0;
      params.gap = Math.max(.25, Number(params.gap) || 4);
      if (recolor) { repaint(first, params.phi1 || []); repaint(second, params.phi2 || []); }
      if (next.beam && next.beam !== lastBeam) setBeam(next.beam);
      beamGroup.visible = params.showBeam !== false;
      waveGroup.visible = !!params.showWaves;
      let visibility = params.layerVisible;
      first.group.visible = visibility === false ? false : typeof visibility === 'object' ? visibility.ms1 !== false && visibility[0] !== false : true;
      second.group.visible = visibility === false ? false : typeof visibility === 'object' ? visibility.ms2 !== false && visibility[1] !== false : true;
      rails.visible = second.group.visible;
      const rec = params.receiver || {};
      const dir = new T.Vector3(Number(rec.ux) || 0, Number(rec.uy) || 0, Number(rec.uz) || 0);
      if (dir.lengthSq() < .001) dir.set(0, 0, 1); dir.normalize();
      const at = dir.multiplyScalar(15.3);
      receiverRay.geometry.setFromPoints([new T.Vector3(), at]); receiverRay.computeLineDistances();
      receiverMarker.position.copy(at); receiverHalo.position.copy(at); receiverLabel.position.copy(at).add(new T.Vector3(0, .8, .9));
    }
    function resetCamera() { orbit.radius = 39; orbit.theta = -.80; orbit.phi = 1.02; target.set(0,0,5); }
    function resize() {
      const r = container.getBoundingClientRect();
      const w = Math.max(1, r.width), h = Math.max(1, r.height);
      if (w !== size.w || h !== size.h) { size = { w, h }; renderer.setSize(w, h, false); camera.aspect = w/h; camera.updateProjectionMatrix(); }
    }
    const observer = new ResizeObserver(resize); observer.observe(container);
    const canvas = renderer.domElement;
    function pointerDown(e) { if (e.button !== 0) return; drag = { x: e.clientX, y: e.clientY }; canvas.setPointerCapture(e.pointerId); canvas.style.cursor = 'grabbing'; }
    function pointerMove(e) { if (!drag) return; orbit.theta -= (e.clientX - drag.x) * .007; orbit.phi = clamp(orbit.phi + (e.clientY - drag.y) * .006, .12, Math.PI - .12); drag = { x: e.clientX, y: e.clientY }; }
    function pointerUp() { drag = null; canvas.style.cursor = 'grab'; }
    function wheel(e) { e.preventDefault(); orbit.radius = clamp(orbit.radius * Math.exp(e.deltaY * .001), 22, 76); }
    canvas.addEventListener('pointerdown', pointerDown); canvas.addEventListener('pointermove', pointerMove);
    canvas.addEventListener('pointerup', pointerUp); canvas.addEventListener('pointercancel', pointerUp); canvas.addEventListener('wheel', wheel, { passive: false });
    canvas.addEventListener('dblclick', resetCamera);
    function render(time) {
      if (disposed) return;
      const dt = Math.min(.06, (time - prevTime) / 1000 || .016); prevTime = time;
      const mix = 1 - Math.exp(-dt * 8);
      smooth.x += (params.shiftX - smooth.x) * mix; smooth.y += (params.shiftY - smooth.y) * mix; smooth.gap += (params.gap - smooth.gap) * mix;
      second.group.position.set(smooth.x, smooth.y, smooth.gap);
      rails.position.z = smooth.gap - .3;
      // The numerical aperture is the complete, fixed MS1 array, including its
      // uncovered cells. Moving MS2 changes the field, not its aperture origin.
      beamGroup.position.set(0, 0, smooth.gap + .2);
      rayGroup.position.copy(beamGroup.position);
      for (let k = 0; k < incomingWaves.length; k++) {
        const progress = ((time / 3000) + k / incomingWaves.length) % 1;
        incomingWaves[k].position.z = -6 + 5.7 * progress;
        incomingWaves[k].material.opacity = .025 + Math.sin(progress * Math.PI) * .16;
      }
      receiverHalo.scale.setScalar(1 + .12 * Math.sin(time / 550));
      // Orbit uses Z-up, consistent with the planar array and propagation axis.
      camera.up.set(0, 0, 1);
      camera.position.set(target.x + orbit.radius * Math.sin(orbit.phi) * Math.cos(orbit.theta),
        target.y + orbit.radius * Math.sin(orbit.phi) * Math.sin(orbit.theta), target.z + orbit.radius * Math.cos(orbit.phi));
      camera.lookAt(target); renderer.render(scene, camera); animation = requestAnimationFrame(render);
    }
    resize(); update({ showWaves: false }); animation = requestAnimationFrame(render);
    return { update, resetCamera, dispose() {
      disposed = true; cancelAnimationFrame(animation); observer.disconnect();
      canvas.removeEventListener('pointerdown', pointerDown); canvas.removeEventListener('pointermove', pointerMove);
      canvas.removeEventListener('pointerup', pointerUp); canvas.removeEventListener('pointercancel', pointerUp); canvas.removeEventListener('wheel', wheel); canvas.removeEventListener('dblclick', resetCamera);
      scene.traverse(obj => { if (obj.geometry) obj.geometry.dispose(); if (obj.material && obj.material.map) obj.material.map.dispose(); });
      for (const material of materials) material.dispose(); if (beamMesh) beamMesh.material.dispose(); if (beamWire) beamWire.material.dispose();
      renderer.dispose(); canvas.remove();
    }};
  };
})();
