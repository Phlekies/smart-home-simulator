import assert from 'node:assert/strict';
import test from 'node:test';
import { wallPoints } from './wallCreation.ts';

test('coordinate entry preserves decimal endpoints exactly without grid snapping', () => {
  assert.deepEqual(wallPoints(1.125, -2.375, 7.0625, 4.8125), [
    { x: 1.125, y: -2.375, z: 0 }, { x: 7.0625, y: 4.8125, z: 0 },
  ]);
});

test('valid horizontal, vertical, diagonal and reversed segments are created at base zero', () => {
  for (const values of [[0, 0, .1, 0], [0, 0, 0, .1], [0, 0, .06, .08], [.1, 0, 0, 0]]) {
    const [start, end] = wallPoints(...values as [number, number, number, number]);
    assert.equal(start.z, 0); assert.equal(end.z, 0);
    assert.ok(Math.abs(Math.hypot(end.x - start.x, end.y - start.y) - .1) < 1e-12);
  }
});

test('a nominal minimum segment remains valid at decimal and large coordinate origins', () => {
  assert.deepEqual(wallPoints(1.1, 2, 1.2, 2), [{ x: 1.1, y: 2, z: 0 }, { x: 1.2, y: 2, z: 0 }]);
  assert.deepEqual(wallPoints(9999.9, -10000, 10000, -10000), [
    { x: 9999.9, y: -10000, z: 0 }, { x: 10000, y: -10000, z: 0 },
  ]);
});

test('degenerate segments and lengths below the practical minimum are rejected', () => {
  for (const values of [[0, 0, 0, 0], [0, 0, .099, 0], [0, 0, .01, .01],
    [10, -8, 10.099999, -8], [-10000, 10000, -9999.901, 10000]]) {
    assert.throws(() => wallPoints(...values as [number, number, number, number]), /0,1 m/);
  }
});

test('contract coordinate boundaries are accepted without clipping', () => {
  assert.deepEqual(wallPoints(-10000, -10000, 10000, 10000), [
    { x: -10000, y: -10000, z: 0 }, { x: 10000, y: 10000, z: 0 },
  ]);
});

test('every coordinate rejects non-finite and out-of-range values', () => {
  for (let index = 0; index < 4; index++) {
    for (const invalid of [NaN, Infinity, -Infinity, -10000.001, 10000.001]) {
      const values: [number, number, number, number] = [0, 0, 1, 1]; values[index] = invalid;
      assert.throws(() => wallPoints(...values), RangeError);
    }
  }
});

test('separate creations do not share mutable point objects', () => {
  const first = wallPoints(0, 0, 1, 1); const second = wallPoints(0, 0, 1, 1);
  first[0].x = 5; first[1].z = 7;
  assert.deepEqual(second, [{ x: 0, y: 0, z: 0 }, { x: 1, y: 1, z: 0 }]);
});
