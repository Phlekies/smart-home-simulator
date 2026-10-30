import assert from 'node:assert/strict';
import test from 'node:test';
import { mapColor, mapExtent, rasterCellSize, validateMapResult } from './coverage.ts';
import { coverageFixture } from './coverageFixture.ts';

test('raster placement retains full-sized grid tiles and clips only the requested edge', () => {
  const { result } = coverageFixture();
  assert.deepEqual(mapExtent(result), { x: 2, y: -3, width: 1.2, height: .2, textureWidth: 2, textureHeight: 1 });
});
test('long narrow grids retain every sample without creating an oversized canvas side', () => {
  for (const [columns, rows] of [[20000, 2], [2, 20000], [200, 200]]) {
    const size = rasterCellSize(columns, rows);
    assert.ok(size >= 1 && Number.isInteger(size));
    assert.ok(columns * size <= 24000 && rows * size <= 24000);
    assert.ok(columns * rows * size ** 2 <= 1440000);
  }
});
test('missing values stay gray and zero margin is a numeric value', () => {
  assert.equal(mapColor(null, 'forward_dbm'), '#737d80');
  assert.equal(mapColor(NaN, 'reverse_dbm'), '#737d80');
  assert.notEqual(mapColor(0, 'forward_margin_db'), mapColor(null, 'forward_margin_db'));
});
test('legend colors saturate at fixed numeric bounds, independent of individual maps', () => {
  assert.equal(mapColor(-120, 'forward_dbm'), mapColor(-100, 'forward_dbm'));
  assert.equal(mapColor(-20, 'reverse_dbm'), mapColor(-30, 'reverse_dbm'));
  assert.equal(mapColor(-40, 'reverse_margin_db'), mapColor(-30, 'reverse_margin_db'));
});
test('matching result retains partial and missing cells without filling values', () => {
  const { request, result } = coverageFixture(); validateMapResult(result, request, result.request_hash);
  assert.deepEqual(result.cells.forward_margin_db, [null, null]);
});
test('a map from another hash or parameter set is rejected', () => {
  const { request, result } = coverageFixture();
  assert.throws(() => validateMapResult(result, request, 'other'));
  for (const mutate of [(r: typeof result) => { r.parameters.grid.height_m = 2; },
    (r: typeof result) => { r.parameters.profile.radio.tx_power_dbm = 20; },
    (r: typeof result) => { r.parameters.access_point_radio_id = 'other'; }]) {
    const changed = structuredClone(result); mutate(changed);
    assert.throws(() => validateMapResult(changed, request, result.request_hash));
  }
});
test('missing arrays, incorrect dimensions and lost exact points cannot be rendered', () => {
  const { request, result } = coverageFixture();
  for (const mutate of [(r: typeof result) => { r.cells.reverse_dbm.pop(); },
    (r: typeof result) => { Reflect.deleteProperty(r.cells, 'forward_dbm'); },
    (r: typeof result) => { r.rows = 2; r.columns = 1; }]) {
    const changed = structuredClone(result); mutate(changed);
    assert.throws(() => validateMapResult(changed, request, result.request_hash));
  }
  request.points.push({ x: 7.125, y: 3.3, z: .4 }); result.parameters.points = [...request.points];
  assert.throws(() => validateMapResult(result, request, result.request_hash));
});
