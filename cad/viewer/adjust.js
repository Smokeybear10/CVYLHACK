/* Sonder: adjust the auto-placed EV charger (or any selected object) in the viewer.
 *
 * Placement is automatic (run.py drops the charger at the swarm-validated curb). This adds the
 * manual adjust the user wants: a panel with drag-on-ground + X / Y / rotate sliders + reset.
 *
 * All moves use the same fragment-proxy pattern Xavier proved in viewer.js (moveCar), so position
 * nudges/sliders are solid. Drag-on-ground and rotate use documented Viewer v7 APIs but want a
 * quick live check once a real scene is loaded (see notes inline). Loaded AFTER viewer.js; shares
 * the page-global `viewer` and `selected`, and reuses `togglePoints`.
 */
(function () {
  const accum = {};        // dbId -> {x, y, yaw} cumulative offset, so "reset" can undo
  let dragMode = false;

  function eachFrag(dbId, fn) {
    const tree = viewer.model.getInstanceTree();
    tree.enumNodeFragments(dbId, (fragId) => {
      const fp = viewer.impl.getFragmentProxy(viewer.model, fragId);
      fp.getAnimTransform();
      fn(fp);
      fp.updateAnimTransform();
    }, true);
    viewer.impl.invalidate(true, true, true);
  }

  function applyDelta(dbId, dx, dy, dyaw) {
    eachFrag(dbId, (fp) => {
      if (dx) fp.position.x += dx;
      if (dy) fp.position.y += dy;
      // NOTE: scene geometry uses absolute world coords, so a quaternion spin pivots about the
      // scene origin, not the object's center. Auto-placement already sets the correct bearing
      // from run.py, so rotate is a fine-tune; verify the pivot live and refine if needed.
      if (dyaw) {
        fp.quaternion.multiply(
          new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), dyaw));
      }
    });
    const a = accum[dbId] || (accum[dbId] = { x: 0, y: 0, yaw: 0 });
    a.x += dx; a.y += dy; a.yaw += dyaw;
  }

  function needSel() {
    if (selected == null) { alert("Select the charger (click it) first"); return false; }
    return true;
  }
  const nudge = (dx, dy) => { if (needSel()) applyDelta(selected, dx, dy, 0); };
  const rotate = (dyaw) => { if (needSel()) applyDelta(selected, 0, 0, dyaw); };
  function reset() {
    if (!needSel()) return;
    const a = accum[selected];
    if (a) applyDelta(selected, -a.x, -a.y, -a.yaw);   // applyDelta zeroes the accumulator
  }

  // object center in world XY, for drag (so the object follows the cursor, not jumps by its origin)
  function center(dbId) {
    const box = new Float32Array(6);
    viewer.model.getInstanceTree().getNodeBox(dbId, box);
    return { x: (box[0] + box[3]) / 2, y: (box[1] + box[4]) / 2 };
  }

  function onMove(ev) {
    if (!dragMode || selected == null) return;
    const hit = viewer.clientToWorld(ev.canvasX ?? ev.offsetX, ev.canvasY ?? ev.offsetY);
    if (!hit || !hit.point) return;            // clientToWorld hits the ground mesh under the cursor
    const c = center(selected);
    applyDelta(selected, hit.point.x - c.x, hit.point.y - c.y, 0);
  }

  function sliderDelta(id, fn) {
    const s = document.getElementById(id);
    s.dataset.prev = "0";
    s.oninput = () => { const v = +s.value, prev = +s.dataset.prev; fn(v - prev); s.dataset.prev = String(v); };
    return s;
  }

  function buildPanel() {
    const p = document.createElement("div");
    p.style.cssText = "position:absolute;z-index:10;bottom:10px;left:10px;background:#111;color:#DEFF00;" +
      "padding:10px 12px;font:12px/1.7 sans-serif;border-radius:6px;min-width:230px";
    p.innerHTML =
      '<div style="font-weight:700;margin-bottom:4px">Adjust charger</div>' +
      '<div style="opacity:.8;margin-bottom:6px">click the charger, then drag or slide</div>' +
      '<label><input type="checkbox" id="sd_drag"> drag on ground</label><br>' +
      '<label>along curb (X) <input type="range" id="sd_x" min="-25" max="25" step="0.25" value="0"></label><br>' +
      '<label>across (Y) <input type="range" id="sd_y" min="-25" max="25" step="0.25" value="0"></label><br>' +
      '<label>rotate <input type="range" id="sd_r" min="-180" max="180" step="5" value="0"></label><br>' +
      '<button id="sd_reset">reset</button> ' +
      '<button id="sd_hide">hide</button> ' +
      '<button id="sd_pts">point cloud</button>';
    document.body.appendChild(p);

    document.getElementById("sd_drag").onchange = (e) => {
      dragMode = e.target.checked;
      if (viewer.setNavigationLock) viewer.setNavigationLock(dragMode);  // freeze orbit while dragging
    };
    sliderDelta("sd_x", (d) => nudge(d, 0));
    sliderDelta("sd_y", (d) => nudge(0, d));
    sliderDelta("sd_r", (d) => rotate((d * Math.PI) / 180));
    document.getElementById("sd_reset").onclick = () => {
      reset();
      ["sd_x", "sd_y", "sd_r"].forEach((id) => { const s = document.getElementById(id); s.value = "0"; s.dataset.prev = "0"; });
    };
    document.getElementById("sd_hide").onclick = () => { if (needSel()) viewer.hide(selected); };
    document.getElementById("sd_pts").onclick = () => { if (typeof togglePoints === "function") togglePoints(); };
    viewer.canvas.addEventListener("mousemove", onMove);
  }

  // wait until viewer.js has loaded the model + instance tree, then attach the panel
  const t = setInterval(() => {
    try {
      if (typeof viewer !== "undefined" && viewer.model && viewer.model.getInstanceTree
          && viewer.model.getInstanceTree()) {
        clearInterval(t);
        buildPanel();
        console.log("Sonder adjust panel ready");
      }
    } catch (e) { /* keep waiting */ }
  }, 400);
})();
