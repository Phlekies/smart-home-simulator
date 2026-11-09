import assert from 'node:assert/strict';
import test from 'node:test';
import { exportSize, MAX_SCALE, panView, scaleBar, visibleBounds, zoomView } from './viewport.ts';

const base = { minX: -2, minY: -2, maxX: 18, maxY: 12 };
const close = (a: number, b: number) => assert.ok(Math.abs(a - b) < 1e-9, `${a} ≠ ${b}`);

test('without zoom the whole plan is visible and panning does nothing', () => {
  assert.deepEqual(visibleBounds(base, null), base);
  assert.equal(panView(base, null, 3, 3), null);
  assert.equal(zoomView(base, null, .5), null, 'zooming out never goes past the whole plan');
});

test('zooming in keeps the anchor point at the same place on screen', () => {
  const anchor = { x: 14, y: 2 };
  const before = visibleBounds(base, null);
  const view = zoomView(base, null, 2, anchor)!;
  const after = visibleBounds(base, view);
  close(after.maxX - after.minX, (before.maxX - before.minX) / 2);
  close((anchor.x - after.minX) / (after.maxX - after.minX), (anchor.x - before.minX) / (before.maxX - before.minX));
  close((anchor.y - after.minY) / (after.maxY - after.minY), (anchor.y - before.minY) / (before.maxY - before.minY));
});

test('zoom is bounded and the visible area never leaves the plan', () => {
  let view = null;
  for (let k = 0; k < 20; k += 1) view = zoomView(base, view, 2, { x: 18, y: 12 });
  assert.equal(view!.scale, MAX_SCALE);
  const moved = visibleBounds(base, panView(base, view, 1000, 1000));
  close(moved.maxX, base.maxX); close(moved.maxY, base.maxY);
  const back = visibleBounds(base, panView(base, view, -1000, -1000));
  close(back.minX, base.minX); close(back.minY, base.minY);
  assert.equal(zoomView(base, view, 1 / MAX_SCALE), null, 'zooming all the way out returns to the fitted plan');
});

test('exported images keep the plan proportions and a bounded size', () => {
  assert.deepEqual(exportSize(base), { width: 1600, height: 1120 });
  assert.deepEqual(exportSize({ minX: 0, minY: 0, maxX: 10, maxY: 40 }), { width: 400, height: 1600 });
});

test('exported scale bar matches the aspect-preserving fit of the rasterized plan', () => {
  const scale = scaleBar(base, { width: 1600, height: 1119 });
  assert.equal(scale.metres, 2);
  close(scale.pixels, 2 * (1119 / 14));
});
