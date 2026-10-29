import assert from 'node:assert/strict';
import test from 'node:test';
import type { Wall } from '../generated/project.ts';
import { transformWall, translateWall, wallLength } from './geometry.ts';

const wall: Wall = {
  id: 'wall-test', start: { x: 1, y: 2, z: .3 }, end: { x: 5, y: 2, z: .3 },
  height_m: 2.6, thickness_m: .18, material_id: 'brick',
};
function close(actual: number, expected: number): void {
  assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} differs from ${expected}`);
}

test('translation preserves length, orientation, elevation and physical properties', () => {
  const moved = translateWall(wall, 3.125, -2.75);
  close(wallLength(moved), 4);
  close(moved.start.x, 4.125);
  close(moved.start.y, -.75);
  close(moved.end.x - moved.start.x, 4);
  assert.equal(moved.start.z, .3);
  assert.equal(moved.material_id, wall.material_id);
  assert.equal(moved.height_m, wall.height_m);
  assert.equal(moved.thickness_m, wall.thickness_m);
  assert.deepEqual(wall.start, { x: 1, y: 2, z: .3 });
  const returned = translateWall(moved, -3.125, 2.75);
  assert.deepEqual(returned, wall);
});

test('rotation/length editing uses the specified centre without changing material or base', () => {
  const vertical = transformWall(wall, 8, 5, 6, 90);
  close(vertical.start.x, 8); close(vertical.start.y, 2);
  close(vertical.end.x, 8); close(vertical.end.y, 8);
  close(wallLength(vertical), 6);
  assert.equal(vertical.start.z, .3);
  assert.equal(vertical.end.z, .3);
  assert.equal(vertical.id, wall.id);
  assert.equal(vertical.material_id, 'brick');
  const restored = transformWall(vertical, 3, 2, 4, 0);
  assert.deepEqual(restored, wall);
});

test('arbitrary angles and minimum supported length remain valid', () => {
  for (const angle of [-720, -45, 13.5, 179, 360, 765]) {
    const result = transformWall(wall, 1.2, -3.4, .1, angle);
    close(wallLength(result), .1);
    close((result.start.x + result.end.x) / 2, 1.2);
    close((result.start.y + result.end.y) / 2, -3.4);
  }
});

test('invalid transformation inputs and resulting out-of-bounds endpoints are rejected', () => {
  for (const length of [0, -.1, .0000009, NaN, Infinity]) {
    assert.throws(() => transformWall(wall, 0, 0, length, 0), RangeError);
  }
  assert.throws(() => transformWall(wall, Infinity, 0, 4, 0), RangeError);
  assert.throws(() => transformWall(wall, 0, 0, 4, NaN), RangeError);
  assert.throws(() => transformWall(wall, 9999, 0, 4, 0), RangeError);
  assert.throws(() => translateWall(wall, 10000, 0), RangeError);
  assert.throws(() => translateWall(wall, NaN, 0), RangeError);
});

test('degenerate or sloping bases cannot be translated into an invalid project', () => {
  assert.throws(() => translateWall({ ...wall, end: { ...wall.start } }, 1, 1), RangeError);
  assert.throws(() => translateWall({ ...wall, end: { ...wall.start, x: wall.start.x + .0000005 } }, 0, 0), RangeError);
  assert.throws(() => translateWall({ ...wall, end: { ...wall.end, z: 1 } }, 1, 1), RangeError);
});

test('short imported segments remain movable and rotatable without being enlarged', () => {
  const imported: Wall = { ...wall, start: { x: 1, y: 2, z: .3 }, end: { x: 1.05, y: 2, z: .3 } };
  const translated = translateWall(imported, 3.125, -2.75);
  close(wallLength(translated), .05);
  close(translated.start.x, 4.125);
  close(translated.start.y, -.75);
  const rotated = transformWall(translated, 2, 4, wallLength(translated), 90);
  close(rotated.start.x, 2); close(rotated.start.y, 3.975);
  close(rotated.end.x, 2); close(rotated.end.y, 4.025);
  close(wallLength(rotated), .05);
  assert.equal(rotated.id, imported.id);
  assert.equal(rotated.height_m, imported.height_m);
  assert.equal(rotated.thickness_m, imported.thickness_m);
  assert.equal(rotated.material_id, imported.material_id);
  assert.equal(rotated.start.z, .3);
  close(wallLength(imported), .05);
});

test('the backend contract minimum remains valid and smaller actual segments are rejected', () => {
  const minimum: Wall = { ...wall, start: { x: 0, y: 0, z: 0 }, end: { x: .000001, y: 0, z: 0 } };
  assert.deepEqual(translateWall(minimum, 0, 0), minimum);
  close(wallLength(transformWall(minimum, 0, 0, .000001, 0)), .000001);
  assert.throws(() => transformWall(minimum, 0, 0, .000000999, 0), RangeError);
});
