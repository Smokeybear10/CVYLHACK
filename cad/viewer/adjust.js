/* Sonder: drag the auto-placed EV charger (or any object) in the Autodesk Viewer.
 *
 * Placement is automatic (run.py drops the charger at the validated curb). This adds plain
 * click-and-drag: grab an object with the mouse and slide it on the ground. No sliders.
 *
 * Structure: a PURE controller (state + math, no THREE/DOM/viewer), unit-tested in Node with a
 * mocked mover (tests/.. adjust.test.js), and a thin BROWSER adapter that backs it with Autodesk
 * fragment proxies (Xavier's moveCar pattern). Works as a browser <script> and a Node module.
 */
(function (root) {
  "use strict";

  // ---------------------------------------------------------------------------
  // PURE controller (unit-tested). Depends only on an injected `mover` and `getCenter`.
  //   mover:      { move(id, dx, dy), rotate(id, dyaw) }
  //   getCenter:  (id) -> { x, y }
  //   onError:    (msg) -> void
  // ---------------------------------------------------------------------------
  function createAdjustController(deps) {
    if (!deps || !deps.mover || !deps.getCenter) throw new Error("createAdjustController: mover and getCenter required");
    var mover = deps.mover;
    var getCenter = deps.getCenter;
    var onError = deps.onError || function () {};
    var accum = {};
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
      // move the selected object so its center sits at world point {x, y}
      dragTo: function (hit) {
        if (!dragMode || selected == null || !hit) return false;
        var c = getCenter(selected);
        if (!c) return false;
        return applyDelta(selected, hit.x - c.x, hit.y - c.y, 0);
      },
    };
  }

  function makeDeltaTracker(initial) {
    var prev = initial || 0;
    return {
      delta: function (value) { var d = value - prev; prev = value; return d; },
      set: function (value) { prev = value || 0; },
    };
  }

  var api = { createAdjustController: createAdjustController, makeDeltaTracker: makeDeltaTracker };
  if (typeof module !== "undefined" && module.exports) { module.exports = api; return; }

  // ---------------------------------------------------------------------------
  // BROWSER adapter: plain click-and-drag, no sliders.
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
  function nodeName(dbId) {
    try { return viewer.model.getInstanceTree().getNodeName(dbId) || ("object " + dbId); }
    catch (e) { return "object " + dbId; }
  }

  function buildHud(onReset) {
    var css = document.createElement("style");
    css.textContent =
      "#sd-hud{position:absolute;z-index:10;bottom:14px;left:14px;background:#0d0f12cc;color:#e9edf2;" +
      "border:1px solid #23272e;border-radius:10px;padding:10px 12px;font:13px/1.5 -apple-system,Segoe UI,sans-serif;" +
      "backdrop-filter:blur(4px);max-width:260px}" +
      "#sd-hud .t{font-weight:700;display:flex;align-items:center;gap:8px}" +
      "#sd-hud .dot{width:8px;height:8px;border-radius:50%;background:#DEFF00}" +
      "#sd-hud .s{font-size:11px;color:#8b94a3;margin:6px 0 8px}" +
      "#sd-hud .s b{color:#DEFF00}" +
      "#sd-hud button{background:#1b1f26;color:#e9edf2;border:1px solid #2b313a;border-radius:6px;" +
      "padding:6px 10px;font:600 12px sans-serif;cursor:pointer;margin-right:6px}" +
      "#sd-hud button:hover{background:#232932}";
    document.head.appendChild(css);
    var h = document.createElement("div");
    h.id = "sd-hud";
    h.innerHTML =
      '<div class="t"><span class="dot"></span>Drag to place</div>' +
      '<div class="s" id="sd-state">Click and drag any object to move it.</div>' +
      '<button id="sd-reset">Reset</button><button id="sd-scan">Scan</button>';
    document.body.appendChild(h);
    document.getElementById("sd-reset").onclick = onReset;
    document.getElementById("sd-scan").onclick = function () { if (typeof togglePoints === "function") togglePoints(); };
    return document.getElementById("sd-state");
  }

  // Multi-part objects (the charger) share a name prefix like "ev_charger_01"; we drag every part
  // of that prefix as one unit. Single objects (a car) are their own one-member group.
  function groupKeyForName(name) {
    var m = name && name.match(/^(ev_charger_\d+)/);
    return m ? m[1] : null;
  }
  function buildGroups() {
    var tree = viewer.model.getInstanceTree();
    var groups = {}, dbToKey = {};
    tree.enumNodeChildren(tree.getRootId(), function (id) {
      if (tree.getChildCount(id) !== 0) return;       // leaves only
      var name = tree.getNodeName(id) || String(id);
      var key = groupKeyForName(name) || ("db_" + id); // charger -> shared key, else its own
      (groups[key] || (groups[key] = [])).push(id);
      dbToKey[id] = key;
    }, true);
    return { groups: groups, dbToKey: dbToKey };
  }

  function init() {
    var G = buildGroups();
    var groupCenter = function (key) {                 // union-box center of all parts in the group
      var ids = G.groups[key] || [];
      var minx = Infinity, miny = Infinity, maxx = -Infinity, maxy = -Infinity;
      ids.forEach(function (id) {
        var c = nodeCenter(id);
        if (c.x < minx) minx = c.x; if (c.x > maxx) maxx = c.x;
        if (c.y < miny) miny = c.y; if (c.y > maxy) maxy = c.y;
      });
      return { x: (minx + maxx) / 2, y: (miny + maxy) / 2 };
    };
    var mover = {
      move: function (key, dx, dy) {
        (G.groups[key] || []).forEach(function (id) {
          eachFrag(id, function (fp) { fp.position.x += dx; fp.position.y += dy; });
        });
      },
      rotate: function () {},                          // rotation handled at generation time (bearing)
    };
    var ctl = createAdjustController({ mover: mover, getCenter: groupCenter, onError: function () {} });
    var stateEl = buildHud(function () { ctl.reset(); });

    function label(key) {
      if (!key) return null;
      return key.indexOf("ev_charger") === 0 ? "EV charger" : key.replace(/^db_/, "object ");
    }
    function setState(key) {
      stateEl.innerHTML = (key == null)
        ? "Click and drag any object to move it."
        : "Holding <b>" + label(key) + "</b> - drag to place";
    }

    var dragging = false, grab = { x: 0, y: 0 };
    var canvas = viewer.canvas;

    canvas.addEventListener("pointerdown", function (ev) {
      if (ev.button !== 0) return;
      var hit = viewer.clientToWorld(ev.offsetX, ev.offsetY);
      var dbId = hit && (hit.dbId != null ? hit.dbId : null);
      if (dbId == null) return;                        // empty space -> let the camera orbit
      var key = G.dbToKey[dbId] || ("db_" + dbId);
      ctl.setSelected(key);
      try { viewer.select(G.groups[key] || [dbId]); } catch (e) {}   // highlight the whole charger
      var c = groupCenter(key), p = hit.point;
      grab.x = c.x - p.x; grab.y = c.y - p.y;          // keep the grabbed point under the cursor
      dragging = true;
      ctl.setDragMode(true);
      if (viewer.setNavigationLock) viewer.setNavigationLock(true);
      setState(key);
      ev.preventDefault();
    });

    canvas.addEventListener("pointermove", function (ev) {
      if (!dragging) return;
      var hit = viewer.clientToWorld(ev.offsetX, ev.offsetY);
      if (hit && hit.point) ctl.dragTo({ x: hit.point.x + grab.x, y: hit.point.y + grab.y });
    });

    function endDrag() {
      if (!dragging) return;
      dragging = false;
      ctl.setDragMode(false);
      if (viewer.setNavigationLock) viewer.setNavigationLock(false);
      setState(ctl.getSelected());
    }
    canvas.addEventListener("pointerup", endDrag);
    window.addEventListener("pointerup", endDrag);

    console.log("Sonder drag ready (groups:", Object.keys(G.groups).length + ")");
  }

  var t = setInterval(function () {
    try {
      if (typeof viewer !== "undefined" && viewer.model && viewer.model.getInstanceTree && viewer.model.getInstanceTree()) {
        clearInterval(t);
        init();
      }
    } catch (e) { /* keep waiting */ }
  }, 400);

})(typeof window !== "undefined" ? window : this);
