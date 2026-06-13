/* Unit tests for the pure adjust controller (no browser, no Autodesk).
 * Run: node --test cad/viewer/adjust.test.js
 *
 * Mocks the mover (the only Autodesk boundary the controller touches) so we can prove the
 * move/rotate/reset/drag math and selection guards exactly, without the live viewer.
 */
const test = require("node:test");
const assert = require("node:assert");
const { createAdjustController, makeDeltaTracker } = require("./adjust.js");

function fakeMover() {
  const pos = {};                 // id -> accumulated {x, y, yaw} the mover actually applied
  const log = [];
  return {
    pos, log,
    move(id, dx, dy) { const p = pos[id] || (pos[id] = { x: 0, y: 0, yaw: 0 }); p.x += dx; p.y += dy; log.push(["move", id, dx, dy]); },
    rotate(id, dyaw) { const p = pos[id] || (pos[id] = { x: 0, y: 0, yaw: 0 }); p.yaw += dyaw; log.push(["rotate", id, dyaw]); },
  };
}
function make(centerMap) {
  const mover = fakeMover();
  const errors = [];
  const ctl = createAdjustController({ mover, getCenter: (id) => (centerMap || {})[id], onError: (m) => errors.push(m) });
  return { ctl, mover, errors };
}

test("constructor requires mover and getCenter", () => {
  assert.throws(() => createAdjustController());
  assert.throws(() => createAdjustController({ mover: {} }));
  assert.doesNotThrow(() => createAdjustController({ mover: {}, getCenter: () => ({}) }));
});

test("nudge with nothing selected is a no-op and reports an error", () => {
  const { ctl, mover, errors } = make();
  assert.strictEqual(ctl.nudge(5, 0), false);
  assert.strictEqual(mover.log.length, 0);
  assert.strictEqual(errors.length, 1);
});

test("select then nudge moves and accumulates", () => {
  const { ctl, mover } = make();
  ctl.setSelected("ev_station_01");
  assert.strictEqual(ctl.nudge(3, 0), true);
  ctl.nudge(0, 2);
  assert.deepStrictEqual(mover.pos["ev_station_01"], { x: 3, y: 2, yaw: 0 });
  assert.deepStrictEqual(ctl.offsetOf("ev_station_01"), { x: 3, y: 2, yaw: 0 });
});

test("rotate accumulates yaw", () => {
  const { ctl, mover } = make();
  ctl.setSelected("c");
  ctl.rotate(0.5);
  ctl.rotate(0.25);
  assert.ok(Math.abs(mover.pos["c"].yaw - 0.75) < 1e-9);
  assert.ok(Math.abs(ctl.offsetOf("c").yaw - 0.75) < 1e-9);
});

test("reset undoes all accumulated movement", () => {
  const { ctl, mover } = make();
  ctl.setSelected("c");
  ctl.nudge(4, -3);
  ctl.rotate(1.0);
  ctl.reset();
  assert.deepStrictEqual(mover.pos["c"], { x: 0, y: 0, yaw: 0 });
  assert.deepStrictEqual(ctl.offsetOf("c"), { x: 0, y: 0, yaw: 0 });
});

test("reset with nothing selected reports an error, no throw", () => {
  const { ctl, errors } = make();
  assert.strictEqual(ctl.reset(), false);
  assert.strictEqual(errors.length, 1);
});

test("drag only moves when drag mode is on", () => {
  const { ctl, mover } = make({ c: { x: 10, y: 5 } });
  ctl.setSelected("c");
  assert.strictEqual(ctl.dragTo({ x: 13, y: 9 }), false);   // drag mode off
  assert.strictEqual(mover.log.length, 0);
  ctl.setDragMode(true);
  assert.strictEqual(ctl.dragTo({ x: 13, y: 9 }), true);     // center (10,5) -> hit (13,9)
  assert.deepStrictEqual(mover.pos["c"], { x: 3, y: 4, yaw: 0 });
});

test("drag is a no-op without a selection or a hit", () => {
  const { ctl } = make({ c: { x: 0, y: 0 } });
  ctl.setDragMode(true);
  assert.strictEqual(ctl.dragTo({ x: 1, y: 1 }), false);     // nothing selected
  ctl.setSelected("c");
  assert.strictEqual(ctl.dragTo(null), false);               // no hit point
});

test("offsets are independent per object", () => {
  const { ctl } = make();
  ctl.setSelected("a"); ctl.nudge(1, 0);
  ctl.setSelected("b"); ctl.nudge(0, 9);
  assert.deepStrictEqual(ctl.offsetOf("a"), { x: 1, y: 0, yaw: 0 });
  assert.deepStrictEqual(ctl.offsetOf("b"), { x: 0, y: 9, yaw: 0 });
});

test("makeDeltaTracker turns absolute slider values into incremental deltas", () => {
  const t = makeDeltaTracker(0);
  assert.strictEqual(t.delta(5), 5);
  assert.strictEqual(t.delta(8), 3);
  assert.strictEqual(t.delta(8), 0);
  assert.strictEqual(t.delta(2), -6);
  t.set(0);
  assert.strictEqual(t.delta(1), 1);
});

test("setSelected(null) clears selection", () => {
  const { ctl } = make();
  ctl.setSelected("c");
  assert.strictEqual(ctl.getSelected(), "c");
  ctl.setSelected(null);
  assert.strictEqual(ctl.getSelected(), null);
});
