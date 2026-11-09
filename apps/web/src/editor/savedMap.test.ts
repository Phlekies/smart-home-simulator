import assert from 'node:assert/strict';
import test from 'node:test';
import { coverageFixture } from './coverageFixture.ts';
import { parseSavedMap, savedMapFileName, savedMapMismatch } from './savedMap.ts';

test('reopens canonical map values, including partial, missing and zero readings', () => {
  const { result } = coverageFixture();
  result.cells.forward_margin_db[0] = 0;
  result.parameters.points = [{ x: 7.125, y: -2, z: 1.4 }];
  result.points = [{ forward_dbm: -70, reverse_dbm: null, forward_margin_db: 0, reverse_margin_db: null,
    status: 'partial', reason: null }];
  assert.deepEqual(parseSavedMap(JSON.stringify(result)), result);
  assert.equal(savedMapFileName(result), 'mapa-bbbbbbbbbb.json');
});

test('rejects invalid JSON, mismatched dimensions, oversized grids and inconsistent values', () => {
  assert.throws(() => parseSavedMap('{'), /JSON válido/);
  assert.throws(() => parseSavedMap('{"maps":[]}'), /mapa de cobertura/);
  const { result } = coverageFixture();
  const inputs = [
    { ...result, columns: 20000, rows: 20000 },
    { ...result, parameters: { ...result.parameters,
      grid: { ...result.parameters.grid, width_m: 2000, depth_m: 2000, resolution_m: .1 } } },
    { ...result, partial_cells: 0 },
    { ...result, cells: { ...result.cells, forward_dbm: [-70, 0] } },
    { ...result, cells: { ...result.cells, status: ['computed', 'not-computed'] } },
    { ...result, cells: { ...result.cells, reverse_dbm: [-80] } },
  ];
  for (const input of inputs) assert.throws(() => parseSavedMap(JSON.stringify(input)), /dimensiones, las celdas/);
});

test('rejects malformed parameter metadata and missing exact samples', () => {
  const { result } = coverageFixture();
  const params = result.parameters;
  assert.throws(() => parseSavedMap(JSON.stringify({ ...result, parameters: {
    ...params, profile: { ...params.profile, radio: { ...params.profile.radio, frequency_hz: 0 } },
  } })), /parámetros/);
  assert.throws(() => parseSavedMap(JSON.stringify({ ...result, parameters: {
    ...params, points: [{ x: 1, y: 2, z: 3 }],
  } })), /puntos exactos/);
});

test('freshness requires matching project, engine and version and a real emitter radio', () => {
  const { result, request } = coverageFixture();
  const fingerprint = { input_hash: result.input_hash, engine: result.engine, engine_version: result.engine_version };
  assert.equal(savedMapMismatch(result, fingerprint, request.project), null);
  assert.match(savedMapMismatch(result, { ...fingerprint, input_hash: 'c'.repeat(64) }, request.project)!, /huella de la instalación/);
  assert.match(savedMapMismatch(result, { ...fingerprint, engine_version: 'later' }, request.project)!, /versión del motor/);
  assert.throws(() => savedMapMismatch(result, { ...fingerprint, input_hash: 'bad' }, request.project), /huella de proyecto válida/);
  request.project.devices[0].radios[0].frequency_hz = 2.437e9;
  assert.throws(() => savedMapMismatch(result, fingerprint, request.project), /radio emisora/);
});
