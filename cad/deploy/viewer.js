let viewer;
let selected = null;
let lidarPoints = null;
let lidarVisible = false;   // start with clean CAD; "Toggle point cloud" shows raw scan

Autodesk.Viewing.Initializer({
  env: "AutodeskProduction2", api: "streamingV2",
  getAccessToken: cb => fetch("/api/token").then(r => r.json())
    .then(t => cb(t.access_token, t.expires_in)),
}, () => {
  viewer = new Autodesk.Viewing.GuiViewer3D(document.getElementById("v"));
  viewer.start();
  viewer.addEventListener(Autodesk.Viewing.SELECTION_CHANGED_EVENT,
    e => selected = e.dbIdArray[0] ?? null);
  viewer.addEventListener(Autodesk.Viewing.OBJECT_TREE_CREATED_EVENT, () => {
    const tree = viewer.model.getInstanceTree();
    let leaves = [];
    tree.enumNodeChildren(tree.getRootId(),
      id => { if (tree.getChildCount(id) === 0) leaves.push(tree.getNodeName(id) || id); },
      true);
    const b = document.createElement("div");
    b.style.cssText = "position:absolute;z-index:9;top:8px;right:8px;background:#DEFF00;padding:4px 8px;font:700 13px sans-serif";
    b.textContent = "objects loaded: " + leaves.length + " [" + leaves.join(", ") + "]";
    document.body.appendChild(b);
    console.log("leaf objects:", leaves);
  });
  Autodesk.Viewing.Document.load("urn:" + URN, doc => {
    // useConsolidation:false — consolidation merges small meshes into shared
    // GPU batches, which makes per-object fragment transforms drag neighbors.
    viewer.loadDocumentNode(doc, doc.getRoot().getDefaultGeometry(),
        { useConsolidation: false })
      .then(loadPointCloud)
      .then(setHumanView);
  }, err => console.error("load failed", err));
});

// Survey data is Z-up (Z = altitude); the viewer defaults to Y-up, which makes
// the home view top-down and first-person "forward" climb vertically.
function setHumanView() {
  viewer.navigation.setWorldUpVector(new THREE.Vector3(0, 0, 1), true);
  const bb = viewer.model.getBoundingBox();
  const c = bb.center();
  const eyeZ = bb.min.z + 2;                       // ~head height above ground
  const eye = new THREE.Vector3(c.x, bb.min.y - 15, eyeZ);
  const target = new THREE.Vector3(c.x, c.y, eyeZ); // look horizontally north
  viewer.navigation.setView(eye, target);
  viewer.navigation.setCameraUpVector(new THREE.Vector3(0, 0, 1));
}

// Raw LiDAR points (XYZ+RGB) rendered inside the APS Viewer as a
// three.js (r71) PointCloud overlay — official APS blog technique.
function loadPointCloud() {
  fetch("/points.bin?v=3").then(r => r.arrayBuffer()).then(buf => {
    const count = new Uint32Array(buf, 0, 1)[0];
    const positions = new Float32Array(buf, 4, count * 3);
    const rgb = new Uint8Array(buf, 4 + count * 12, count * 3);
    const colors = new Float32Array(count * 3);
    for (let i = 0; i < count * 3; i++) colors[i] = rgb[i] / 255;

    const geometry = new THREE.BufferGeometry();
    geometry.addAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.addAttribute("color", new THREE.BufferAttribute(colors, 3));
    geometry.computeBoundingBox();
    geometry.isPoints = true;   // force gl.POINTS rendering in the Viewer

    const material = new THREE.PointCloudMaterial({
      size: 0.25, vertexColors: THREE.VertexColors,
    });
    const points = new THREE.PointCloud(geometry, material);
    // The viewer shifts the SVF2 model by a global offset (and placement
    // transform); apply the same to the overlay so points align with the model.
    const data = viewer.model.getData();
    if (data.placementWithOffset) {
      points.applyMatrix(data.placementWithOffset);
    } else if (data.globalOffset) {
      points.position.set(-data.globalOffset.x, -data.globalOffset.y, -data.globalOffset.z);
    }
    lidarPoints = points;
    viewer.impl.createOverlayScene("lidar");
    if (lidarVisible) viewer.impl.addOverlay("lidar", points);
    viewer.impl.invalidate(true, true, true);
    console.log("lidar overlay ready:", count, "points (hidden by default)");
  }).catch(err => console.error("points.bin load failed", err));
}

function togglePoints() {
  if (!lidarPoints) return;
  lidarVisible = !lidarVisible;
  if (lidarVisible) viewer.impl.addOverlay("lidar", lidarPoints);
  else viewer.impl.removeOverlay("lidar", lidarPoints);
  viewer.impl.invalidate(true, true, true);
}

function moveCar() {
  if (selected == null) return alert("Select a car first");
  const tree = viewer.model.getInstanceTree();
  tree.enumNodeFragments(selected, fragId => {
    const fp = viewer.impl.getFragmentProxy(viewer.model, fragId);
    fp.getAnimTransform();
    fp.position.x += 5;            // slide 5 m along X
    fp.updateAnimTransform();
  });
  viewer.impl.invalidate(true, true, true);
}

function deleteCar() {
  if (selected == null) return alert("Select a car first");
  viewer.hide(selected);
}

/* =========================================================================
 * ADDITIVE PRESENTATION LAYER — entrance fit, idle auto-orbit, charger
 * beacon, point-cloud fade. Pure vanilla + the viewer's own three.js (r71).
 * Everything is guarded so a missing dbId or API timing never throws and
 * breaks the load. Nothing above this line is modified.
 * ========================================================================= */
(function () {
  const REDUCED =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Wait until `viewer` exists and is started, then fire cb(viewer) once.
  function whenViewerReady(cb) {
    let tries = 0;
    (function poll() {
      if (typeof viewer !== "undefined" && viewer && viewer.impl) {
        try { cb(viewer); } catch (e) { console.warn("[anim] init skipped", e); }
        return;
      }
      if (tries++ > 200) return; // ~20s ceiling, then give up silently
      setTimeout(poll, 100);
    })();
  }

  whenViewerReady(function (v) {
    const E = Autodesk.Viewing;

    /* ---- 1. smooth fit-to-view fly-in on GEOMETRY_LOADED ----------------
     * setHumanView() already places the first-person eye. We layer a gentle
     * eased settle on top: nudge out, then ease back to the framed view so
     * the scene "arrives" instead of snapping. Runs once.                  */
    let flewIn = false;
    function flyIn() {
      if (flewIn) return;
      flewIn = true;
      if (REDUCED) return;
      try {
        const nav = v.navigation;
        const startEye = nav.getPosition().clone();
        const target = nav.getTarget().clone();
        const dir = startEye.clone().sub(target);
        const len = dir.length() || 1;
        dir.multiplyScalar(1.18 / len);              // pull back ~18%
        const wideEye = target.clone().add(dir.multiplyScalar(len));

        const dur = 1100, t0 = performance.now();
        const ease = x => 1 - Math.pow(1 - x, 3);    // easeOutCubic
        nav.setView(wideEye, target);
        (function step(now) {
          const k = Math.min(1, (now - t0) / dur);
          const e = ease(k);
          const ex = wideEye.x + (startEye.x - wideEye.x) * e;
          const ey = wideEye.y + (startEye.y - wideEye.y) * e;
          const ez = wideEye.z + (startEye.z - wideEye.z) * e;
          try {
            nav.setPosition(new THREE.Vector3(ex, ey, ez));
            nav.setTarget(target);
          } catch (_) {}
          if (k < 1) requestAnimationFrame(step);
          else idleOrbit.arm();                       // hand off to auto-orbit
        })(t0);
      } catch (e) {
        console.warn("[anim] fly-in skipped", e);
      }
    }
    v.addEventListener(E.GEOMETRY_LOADED_EVENT, flyIn);
    // GEOMETRY_LOADED may already have fired before this listener attached.
    if (v.model && v.model.getInstanceTree && v.model.getInstanceTree())
      flyIn();

    /* ---- 2. gentle continuous auto-orbit, pauses on interaction --------- */
    const idleOrbit = (function () {
      const IDLE_MS = 2600;        // resume this long after last interaction
      const SPEED = 0.04;          // radians / second — slow drift
      let armed = false, running = false, last = 0, lastInput = 0, raf = 0;
      let suppress = false;        // ignore camera events we cause ourselves

      function onInput() {
        lastInput = performance.now();
        running = false;
      }
      // User interaction signals.
      ["mousedown", "wheel", "touchstart", "keydown"].forEach(ev =>
        v.container && v.container.addEventListener(ev, onInput, { passive: true })
      );
      v.addEventListener(E.CAMERA_CHANGE_EVENT, () => { if (!suppress) onInput(); });

      function frame(now) {
        raf = requestAnimationFrame(frame);
        const dt = (now - (last || now)) / 1000;
        last = now;
        if (now - lastInput < IDLE_MS) return;       // still cooling down
        try {
          const nav = v.navigation;
          const eye = nav.getPosition();
          const tgt = nav.getTarget();
          const up = nav.getWorldUpVector ? nav.getWorldUpVector() : new THREE.Vector3(0, 0, 1);
          // rotate eye around target about the world-up axis
          const off = eye.clone().sub(tgt);
          const ang = SPEED * Math.min(dt, 0.1);
          const q = new THREE.Quaternion().setFromAxisAngle(up.clone().normalize(), ang);
          off.applyQuaternion(q);
          suppress = true;
          nav.setPosition(tgt.clone().add(off));
          nav.setTarget(tgt);
          suppress = false;
        } catch (_) { suppress = false; }
      }

      return {
        arm() {
          if (armed || REDUCED) return;
          armed = true;
          lastInput = performance.now();
          raf = requestAnimationFrame(frame);
        }
      };
    })();
    if (flewIn && !REDUCED) idleOrbit.arm();          // covers already-loaded case

    /* ---- 3. pulsing locator beacon on EV charger object(s) -------------- */
    (function chargerBeacon() {
      let beaconStarted = false;
      function findChargerIds() {
        const ids = [];
        try {
          const tree = v.model && v.model.getInstanceTree && v.model.getInstanceTree();
          if (!tree) return ids;
          const re = /(charg|\bev\b| evse|plug|station)/i;
          tree.enumNodeChildren(tree.getRootId(), id => {
            if (tree.getChildCount(id) === 0) {
              const name = tree.getNodeName(id) || "";
              if (re.test(name)) ids.push(id);
            }
          }, true);
        } catch (_) {}
        return ids;
      }

      function start(ids) {
        if (!ids.length || beaconStarted) return;
        beaconStarted = true;
        const CYAN = new THREE.Vector4(0.204, 0.890, 0.831, 1); // #34e3d4
        const apply = intensity => {
          const col = new THREE.Vector4(CYAN.x, CYAN.y, CYAN.z, intensity);
          try {
            ids.forEach(id => v.setThemingColor(id, col, v.model, true));
            v.impl.invalidate(true, false, false);
          } catch (_) {}
        };
        if (REDUCED) { apply(0.5); return; }          // static highlight, no loop
        const t0 = performance.now();
        (function pulse(now) {
          requestAnimationFrame(pulse);
          // 0..1 sinusoid, ~1.6s period
          const s = (Math.sin((now - t0) / 1600 * Math.PI * 2) + 1) / 2;
          apply(0.25 + s * 0.75);
        })(t0);
      }

      function tryStart() {
        const ids = findChargerIds();
        if (ids.length) { start(ids); return true; }
        return false;
      }

      if (!tryStart()) {
        v.addEventListener(E.OBJECT_TREE_CREATED_EVENT, tryStart);
        v.addEventListener(E.GEOMETRY_LOADED_EVENT, tryStart);
      }
    })();
  });

  /* ---- 5. fade the point cloud in when toggled on ----------------------
   * Wraps the existing global togglePoints() additively; if the overlay
   * material exposes opacity, ramp it 0 -> 1. Falls back to the original
   * behavior untouched if anything is unavailable.                        */
  const _origToggle = typeof togglePoints === "function" ? togglePoints : null;
  if (_origToggle) {
    window.togglePoints = function () {
      const becomingVisible = !lidarVisible;          // read state before toggle
      _origToggle();                                  // original add/remove + invalidate
      if (REDUCED || !becomingVisible) return;
      try {
        const mat = lidarPoints && lidarPoints.material;
        if (!mat) return;
        mat.transparent = true;
        mat.opacity = 0;
        const dur = 600, t0 = performance.now();
        (function ramp(now) {
          const k = Math.min(1, (now - t0) / dur);
          mat.opacity = k;
          if (viewer && viewer.impl) viewer.impl.invalidate(true, false, false);
          if (k < 1) requestAnimationFrame(ramp);
        })(t0);
      } catch (_) {}
    };
  }
})();
