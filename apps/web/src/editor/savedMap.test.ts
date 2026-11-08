import assert from 'node:assert/strict';
import test from 'node:test';
import { coverageFixture } from './coverageFixture.ts';
import { parseSavedMap, savedMapFileName, savedMapStaleness } from './savedMap.ts';

const fingerprint = (changes = {}) => ({ input_hash: 'a'.repeat(64), engine: 'quick-estimate' as const, engine_version: 'test', ...changes });

test('a saved map round-trips through its JSON file', () => {
  const { result } = coverageFixture();
  const parsed = parseSavedMap(JSON.stringify(result));
  assert.deepEqual(parsed, result);
  assert.equal(savedMapFileName(parsed), 'mapa-bbbbbbbbbb.json');
});

test('files that are not maps, or whose cells do not match the grid, are refused', () => {
  const { result } = coverageFixture();
  assert.throws(() => parseSavedMap('{not json'), /JSON válido/);
  assert.throws(() => parseSavedMap(JSON.stringify({ name: 'a project' })), /No es un mapa guardado/);
  const { input_hash: _hash, ...withoutHash } = result;
  assert.throws(() => parseSavedMap(JSON.stringify(withoutHash)), /huella/);
  const truncated = structuredClone(result); truncated.cells.status.pop();
  assert.throws(() => parseSavedMap(JSON.stringify(truncated)), /no coinciden con su rejilla/);
});

test('a saved map is current only with the same project hash and engine version', () => {
  const { result } = coverageFixture();
  assert.equal(savedMapStaleness(result, fingerprint()), null);
  assert.match(savedMapStaleness(result, fingerprint({ input_hash: 'c'.repeat(64) }))!, /proyecto ha cambiado/);
  assert.match(savedMapStaleness(result, fingerprint({ engine_version: '0.2.0' }))!, /motor test; el actual es 0\.2\.0/);
});
