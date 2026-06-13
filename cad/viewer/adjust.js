/* Sonder: adjust the auto-placed EV charger in the Autodesk Viewer.
 *
 * Placement is automatic (run.py drops the charger at the swarm-validated curb). This adds the
 * manual adjust: select the charger, then drag it on the ground or use X / Y / rotate sliders.
 *
 * Structure: a PURE controller (state + math, no THREE / DOM / viewer) that is unit-tested in Node
 * with a mocked mover (tests/test_adjust.js), and a thin BROWSER adapter that backs the controller
 * with Autodesk fragment proxies (the pattern Xavier proved in viewer.js:moveCar) and builds the
 * panel. The file works as a browser <script> and as a Node module (for the tests).
 */
(function (root) {
  "use strict";

  // ---------------------------------------------------------------------------
  // PURE controller (unit-tested). Depends only on an injected `mover` and `getCenter`.
  //   mover:      { move(id, dx, dy), rotate(id, dyaw) }
  //   getCenter:  (id) -> { x, y }  (object center in world XY, for drag)
  //   onError:    (msg) -> void     (e.g. alert)
  // ---------------------------------------------------------------------------
  function createAdjustController(deps) {
    if (!deps || !deps.mover || !deps.getCenter) throw new Error("createAdjustController: mover and getCenter required");
    var mover = deps.mover;
    var getCenter = deps.getCenter;
    var onError = deps.onError || function () {};
    var accum = {};          // dbId -> {x, y, yaw} cumulative offset, so reset can undo
    var selected = null;
    var dragMode = false;

    function applyDelta(id, dx, dy, dyaw) {
      if (id == null) return false;
      if (dx || dy) mover.move(id, dx, dy);
      if (dyaw) mover.rotate(id, dyaw);
      var a = accum[id] || (accum[id] = { x: 0, y: 0, yaw: 0 });
      a.x += dx; a.y += dy; a.yaw += dyaw;
      return true;
    }
    function requireSel() {
      if (selected == null) { onError("Select the charger (click it) first"); return false; }
      return true;
    }

    return {
      setSelected: function (id) { selected = (id == null ? null : id); },
      getSelected: function () { return selected; },
      setDragMode: function (on) { dragMode = !!on; },
      isDragMode: function () { return dragMode; },
      nudge: function (dx, dy) { return requireSel() ? applyDelta(selected, dx, dy, 0) : false; },
      rotate: function (dyaw) { return requireSel() ? applyDelta(selected, 0, 0, dyaw) : false; },
      reset: function () {
        if (!requireSel()) return false;
        var a = accum[selected];
        if (a && (a.x || a.y || a.yaw)) applyDelta(selected, -a.x, -a.y, -a.yaw);
        return true;
      },
      offsetOf: function (id) { var a = accum[id]; return a ? { x: a.x, y: a.y, yaw: a.yaw } : { x: 0, y: 0, yaw: 0 }; },
      // drag: move the selected object so its center sits under the cursor's ground hit
      dragTo: function (hit) {
        if (!dragMode || selected == null || !hit) return false;
        var c = getCenter(selected);
        if (!c) return false;
        return applyDelta(selected, hit.x - c.x, hit.y - c.y, 0);
      },
    };
  }

  // A slider emits absolute values; this turns them into incremental deltas.
  function makeDeltaTracker(initial) {
    var prev = initial || 0;
    return {
      delta: function (value) { var d = value - prev; prev = value; return d; },
      set: function (value) { prev = value || 0; },
    };
  }

  var api = { createAdjustController: createAdjustController, makeDeltaTracker: makeDeltaTracker };

  // Node (tests): export and stop. Browser globals are never touched here.
  if (typeof module !== "undefined" && module.exports) { module.exports = api; return; }

  // ---------------------------------------------------------------------------
  // BROWSER adapter: wire the controller to the real Autodesk Viewer + THREE.
  // ---------------------------------------------------------------------------
  root.SonderAdjust = api;

  function eachFrag(dbId, fn) {
    var tree = viewer.model.getInstanceTree();
    tree.enumNodeFragments(dbId, function (fragId) {
      var fp = viewer.impl.getFragmentProxy(viewer.model, fragId);
      fp.getAnimTransform();
      fn(fp);
      fp.updateAnimTransform();
    }, true);
    viewer.impl.invalidate(true, true, true);
  }
  function nodeCenter(dbId) {
    var box = new Float32Array(6);
    viewer.model.getInstanceTree().getNodeBox(dbId, box);
    return { x: (box[0] + box[3]) / 2, y: (box[1] + box[4]) / 2 };
  }

  function injectStyles() {
    var css = document.createElement("style");
    css.textContent = [
      "#sd-panel{position:absolute;z-index:10;bottom:14px;left:14px;width:248px;",
      "background:#0d0f12;color:#e9edf2;border:1px solid #23272e;border-radius:10px;",
      "box-shadow:0 8px 28px rgba(0,0,0,.45);font:13px/1.5 -apple-system,Segoe UI,sans-serif;overflow:hidden}",
      "#sd-panel .sd-h{background:#15181d;padding:10px 12px;font-weight:700;letter-spacing:.2px;",
      "border-bottom:1px solid #23272e;display:flex;align-items:center;gap:8px}",
      "#sd-panel .sd-dot{width:8px;height:8px;border-radius:50%;background:#DEFF00}",
      "#sd-panel .sd-body{padding:12px}",
      "#sd-panel .sd-sel{font-size:11px;color:#8b94a3;margin-bottom:10px;min-height:14px}",
      "#sd-panel .sd-sel b{color:#DEFF00;font-weight:600}",
      "#sd-panel .sd-row{display:flex;align-items:center;gap:8px;margin:8px 0}",
      "#sd-panel .sd-row label{flex:0 0 64px;color:#aeb6c2}",
      "#sd-panel input[type=range]{flex:1;accent-color:#DEFF00;cursor:pointer}",
      "#sd-panel .sd-val{flex:0 0 42px;text-align:right;font-variant-numeric:tabular-nums;color:#cfd6df}",
      "#sd-panel .sd-drag{display:flex;align-items:center;gap:8px;margin:2px 0 10px;cursor:pointer;user-select:none}",
      "#sd-panel .sd-btns{display:flex;gap:6px;margin-top:12px}",
      "#sd-panel button{flex:1;background:#1b1f26;color:#e9edf2;border:1px solid #2b313a;",
      "border-radius:6px;padding:7px 0;font:600 12px sans-serif;cursor:pointer}",
      "#sd-panel button:hover{background:#232932;border-color:#3a424e}",
      "#sd-panel button.sd-primary{background:#DEFF00;color:#0d0f12;border-color:#DEFF00}",
      "#sd-panel button.sd-primary:hover{filter:brightness(.94)}",
    ].join("");
    document.head.appendChild(css);
  }

  function row(label, id, min, max, step, unit) {
    return '<div class="sd-row"><label>' + label + '</label>' +
      '<input type="range" id="' + id + '" min="' + min + '" max="' + max + '" step="' + step + '" value="0">' +
      '<span class="sd-val" id="' + id + 'v">0' + unit + '</span></div>';
  }

  function buildPanel(ctl) {
    injectStyles();
    var p = document.createElement("div");
    p.id = "sd-panel";
    p.innerHTML =
      '<div class="sd-h"><span class="sd-dot"></span>Adjust charger</div>' +
      '<div class="sd-body">' +
      '<div class="sd-sel" id="sd-sel">Click the charger to select it.</div>' +
      '<label class="sd-drag"><input type="checkbox" id="sd-drag"> drag on ground</label>' +
      row("along curb", "sd-x", -25, 25, 0.25, " m") +
      row("across", "sd-y", -25, 25, 0.25, " m") +
      row("rotate", "sd-r", -180, 180, 5, "&deg;") +
      '<div class="sd-btns">' +
      '<button id="sd-reset">Reset</button>' +
      '<button id="sd-hide">Hide</button>' +
      '<button class="sd-primary" id="sd-pts">Scan</button>' +
      '</div></div>';
    document.body.appendChild(p);

    var sel = document.getElementById("sd-sel");
    var sx = document.getElementById("sd-x"), sy = document.getElementById("sd-y"), sr = document.getElementById("sd-r");
    var sxv = document.getElementById("sd-xv"), syv = document.getElementById("sd-yv"), srv = document.getElementById("sd-rv");
    var tx = makeDeltaTracker(0), ty = makeDeltaTracker(0), tr = makeDeltaTracker(0);

    function resetSliders() {
      [sx, sy, sr].forEach(function (s) { s.value = "0"; });
      tx.set(0); ty.set(0); tr.set(0);
      sxv.textContent = "0 m"; syv.textContent = "0 m"; srv.innerHTML = "0&deg;";
    }

    // keep our notion of selection in sync, show the object's name, reset sliders per object
    viewer.addEventListener(Autodesk.Viewing.SELECTION_CHANGED_EVENT, function (e) {
      var id = (e.dbIdArray && e.dbIdArray.length) ? e.dbIdArray[0] : null;
      ctl.setSelected(id);
      if (id == null) { sel.textContent = "Click the charger to select it."; }
      else {
        var name = viewer.model.getInstanceTree().getNodeName(id) || ("object " + id);
        sel.innerHTML = "Selected: <b>" + name + "</b>";
      }
      resetSliders();
    });

    document.getElementById("sd-drag").onchange = function (ev) {
      ctl.setDragMode(ev.target.checked);
      if (viewer.setNavigationLock) viewer.setNavigationLock(ev.target.checked);
    };
    sx.oninput = function () { ctl.nudge(tx.delta(+sx.value), 0); sxv.textContent = (+sx.value).toFixed(2) + " m"; };
    sy.oninput = function () { ctl.nudge(0, ty.delta(+sy.value)); syv.textContent = (+sy.value).toFixed(2) + " m"; };
    sr.oninput = function () { ctl.rotate(tr.delta(+sr.value) * Math.PI / 180); srv.innerHTML = (+sr.value) + "&deg;"; };
    document.getElementById("sd-reset").onclick = function () { ctl.reset(); resetSliders(); };
    document.getElementById("sd-hide").onclick = function () {
      var id = ctl.getSelected();
      if (id == null) return alert("Select the charger first");
      viewer.hide(id);
    };
    document.getElementById("sd-pts").onclick = function () { if (typeof togglePoints === "function") togglePoints(); };

    viewer.canvas.addEventListener("pointermove", function (ev) {
      if (!ctl.isDragMode()) return;
      var hit = viewer.clientToWorld(ev.offsetX, ev.offsetY);
      if (hit && hit.point) ctl.dragTo({ x: hit.point.x, y: hit.point.y });
    });
  }

  function init() {
    var mover = {
      move: function (id, dx, dy) { eachFrag(id, function (fp) { fp.position.x += dx; fp.position.y += dy; }); },
      rotate: function (id, dyaw) {
        eachFrag(id, function (fp) {
          fp.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), dyaw));
        });
      },
    };
    var ctl = createAdjustController({ mover: mover, getCenter: nodeCenter, onError: function (m) { alert(m); } });
    buildPanel(ctl);
    console.log("Sonder adjust panel ready");
  }

  // attach once viewer.js has loaded the model + instance tree
  var t = setInterval(function () {
    try {
      if (typeof viewer !== "undefined" && viewer.model && viewer.model.getInstanceTree && viewer.model.getInstanceTree()) {
        clearInterval(t);
        init();
      }
    } catch (e) { /* keep waiting */ }
  }, 400);

})(typeof window !== "undefined" ? window : this);
