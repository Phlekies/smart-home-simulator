import assert from 'node:assert/strict';
import test from 'node:test';
import type { Project, Radio } from '../generated/project.ts';
import type { DirectionResult, SimulationResult } from '../generated/simulation-result.ts';
import { captureComparison, comparePositions, movedDevices, samePositionConfiguration } from './comparison.ts';
import { makeReference } from './referencePersistence.ts';

const radio: Radio = { id: 'r', protocol: 'wifi', frequency_hz: 2.412e9, bandwidth_hz: 20e6, channel: 1,
  tx_power_dbm: 10, tx_gain_dbi: 0, rx_gain_dbi: 0, sensitivity_dbm: null, noise_figure_db: 7,
  antenna: 'omnidirectional', orientation_deg: 0, beamwidth_deg: 360, pattern_sharpness: 1.8,
  side_lobe_attenuation_db: 18, polarization_deg: 0 };
function project(): Project {
  return { format: 'smart-environment-simulator', version: 1, units: 'm', name: 'Synthetic comparison fixture',
    building: { width_m: 10, depth_m: 10, materials: [{ id: 'm', name: 'Synthetic material', loss_db_24ghz: 3,
      loss_db_5ghz: 5, extra_loss_db_per_cm: 0, evidence: 'Unit test only' }], walls: [{ id: 'w', material_id: 'm',
        start: { x: 0, y: 2, z: 0 }, end: { x: 10, y: 2, z: 0 }, thickness_m: .12, height_m: 2.6 }] },
    devices: ['a', 'b'].map((id, index) => ({ id, name: id, role: 'endpoint', evidence: 'Unit test only',
      position: { x: index * 2, y: 1, z: 1.4 }, radios: [structuredClone(radio)] })),
    links: [{ id: 'l', source_device_id: 'a', source_radio_id: 'r', target_device_id: 'b', target_radio_id: 'r' }],
    settings: { path_loss_exponent: 2.1, extra_loss_db_per_m: 0, system_gain_db: 0 },
    migration_notes: [], legacy_source: { untouched: true } };
}
// These numbers are synthetic arithmetic test vectors, not predictions or measurements.
function direction(tx = 'a', rx = 'b', power = -70, margin: number | null = null): DirectionResult {
  return { tx_device_id: tx, rx_device_id: rx, distance_m: 2, path_loss_db: 70, wall_loss_db: 0,
    crossed_wall_ids: [], received_power_dbm: power, noise_dbm: -90, snr_db: 20, margin_db: margin };
}
function result(hash = 'a'.repeat(64)): SimulationResult {
  return { engine: 'quick-estimate', engine_version: 'test', input_hash: hash, elapsed_ms: 1,
    scope: 'Synthetic test', limitations: ['No field validation'], links: [{ id: 'l', compatibility: 'unverified',
      status: 'unverified', forward: direction(), reverse: direction('b', 'a', -80) , reasons: ['Unknown sensitivity'] }] };
}
const base = () => captureComparison(project(), result(), '2026-10-30T09:00:00Z');
function moved() { const p = project(); p.devices[0].position = { x: 1.125, y: 1, z: 2.375 }; return p; }

test('base is detached from subsequent project and result edits', () => {
  const p = project(), r = result(), snapshot = captureComparison(p, r);
  p.devices[0].position.x = 6; r.links[0].forward!.received_power_dbm = -10;
  assert.equal(snapshot.project.devices[0].position.x, 0);
  assert.equal(snapshot.result.links[0].forward!.received_power_dbm, -70);
});

test('position and height changes are comparable; names and object ordering do not change conditions', () => {
  const p = moved(); p.name = 'Alternative'; p.devices[0].name = 'AP'; p.devices.reverse();
  assert.equal(samePositionConfiguration(project(), p), true);
  const moves = movedDevices(project(), p);
  assert.equal(moves.length, 1); assert.equal(moves[0].name, 'AP');
  assert.deepEqual(moves[0].to, { x: 1.125, y: 1, z: 2.375 });
  moves[0].to.x = 50; assert.equal(p.devices[1].position.x, 1.125);
});

test('radio, material, wall, topology and setting changes block a placement comparison', () => {
  const edits = [(p: Project) => { p.devices[0].radios[0].tx_power_dbm = 20; },
    (p: Project) => { p.devices[0].radios[0].sensitivity_dbm = -90; },
    (p: Project) => { p.devices[0].radios[0].frequency_hz = 5e9; },
    (p: Project) => { p.building.materials[0].loss_db_24ghz = 10; },
    (p: Project) => { p.building.walls[0].start.x = 3; },
    (p: Project) => { p.links[0].source_radio_id = 'other'; },
    (p: Project) => { p.settings.path_loss_exponent = 3; },
    (p: Project) => { p.devices.pop(); }];
  for (const edit of edits) {
    const p = moved(); edit(p);
    assert.equal(samePositionConfiguration(project(), p), false);
    assert.equal(comparePositions(base(), p, result('b'.repeat(64))).kind, 'blocked');
  }
});

test('a calibrated background image does not change the physical conditions of a placement comparison', () => {
  const p = moved();
  p.plan_reference = makeReference({ url: 'blob:test', fileName: 'synthetic.png', mediaType: 'image/png',
    sha256: 'a'.repeat(64), widthPx: 800, heightPx: 600 }, { x: 0, y: 0 }, { x: 600, y: 0 }, 12,
    { originX: -2.125, originY: 3.75 });
  assert.equal(samePositionConfiguration(project(), p), true);
  assert.equal(comparePositions(base(), p, result('b'.repeat(64))).kind, 'ready');
});

test('an edited alternative without a fresh result hides deltas and retains the base', () => {
  const snapshot = base(); assert.equal(comparePositions(snapshot, moved(), null).kind, 'waiting');
  assert.equal(snapshot.result.input_hash, 'a'.repeat(64));
});

test('both directions retain their own sign and unknown margins remain unknown', () => {
  const current = result('b'.repeat(64)); current.links[0].forward!.received_power_dbm = -62.5;
  current.links[0].reverse!.received_power_dbm = -84;
  const compared = comparePositions(base(), moved(), current);
  assert.equal(compared.kind, 'ready'); if (compared.kind !== 'ready') return;
  assert.deepEqual(compared.rows.map(row => [row.txName, row.rxName, row.power.delta]), [['a', 'b', 7.5], ['b', 'a', -4]]);
  assert.deepEqual(compared.rows[0].margin, { base: null, alternative: null, delta: null });
  assert.equal(compared.rows[0].baseStatus, 'unverified'); assert.equal(compared.rows[0].alternativeStatus, 'unverified');
});

test('zero margins and negative margins are numeric; no truthiness fallback', () => {
  const snapshot = base(); snapshot.result.links[0].forward!.margin_db = 0;
  const current = result('b'.repeat(64)); current.links[0].forward!.margin_db = -4;
  const compared = comparePositions(snapshot, moved(), current);
  assert.equal(compared.kind, 'ready'); if (compared.kind !== 'ready') return;
  assert.deepEqual(compared.rows[0].margin, { base: 0, alternative: -4, delta: -4 });
});

test('missing directions and non-finite values never produce a fabricated difference', () => {
  const snapshot = base(); snapshot.result.links[0].forward = null;
  const current = result('b'.repeat(64)); current.links[0].reverse!.received_power_dbm = NaN;
  const compared = comparePositions(snapshot, moved(), current);
  assert.equal(compared.kind, 'ready'); if (compared.kind !== 'ready') return;
  assert.equal(compared.rows[0].power.base, null); assert.equal(compared.rows[0].power.delta, null);
  assert.equal(compared.rows[1].power.alternative, null); assert.equal(compared.rows[1].power.delta, null);
});

test('engine and version mismatches require a new base', () => {
  for (const [key, value] of [['engine', 'other'], ['engine_version', 'other']] as const) {
    const current = result('b'.repeat(64)); current[key] = value;
    assert.equal(comparePositions(base(), moved(), current).kind, 'blocked');
  }
});

test('missing, duplicated, foreign or reversed link result identities block the table', () => {
  for (const mutate of [(r: SimulationResult) => { r.links = []; },
    (r: SimulationResult) => { r.links.push(structuredClone(r.links[0])); },
    (r: SimulationResult) => { r.links[0].id = 'foreign'; },
    (r: SimulationResult) => { r.links[0].forward!.tx_device_id = 'b'; }]) {
    const current = result('b'.repeat(64)); mutate(current);
    assert.equal(comparePositions(base(), moved(), current).kind, 'blocked');
  }
});

test('an unchanged input hash cannot be reused after moving a device', () => {
  assert.equal(comparePositions(base(), moved(), result()).kind, 'blocked');
  const compared = comparePositions(base(), project(), result());
  assert.equal(compared.kind, 'ready'); if (compared.kind !== 'ready') return;
  assert.equal(compared.rows[0].power.delta, 0);
});

test('a project with no links cannot claim a completed comparison', () => {
  const p = project(); p.links = []; const r = result(); r.links = [];
  assert.equal(comparePositions(captureComparison(p, r), p, r).kind, 'blocked');
});

test('parallel links between the same devices keep their radio identities and results separate', () => {
  const p = project(); p.devices[0].radios.push({ ...radio, id: 'second' });
  p.links.push({ ...p.links[0], id: 'l2', source_radio_id: 'second' });
  const before = result(); before.links.push({ ...structuredClone(before.links[0]), id: 'l2' });
  const after = structuredClone(before); after.input_hash = 'b'.repeat(64);
  after.links[1].forward!.received_power_dbm = -60;
  const alternative = structuredClone(p); alternative.devices[0].position.x = 1;
  const compared = comparePositions(captureComparison(p, before), alternative, after);
  assert.equal(compared.kind, 'ready'); if (compared.kind !== 'ready') return;
  assert.deepEqual(compared.rows.map(row => [row.linkId, row.txRadioId, row.rxRadioId, row.power.delta]), [
    ['l', 'r', 'r', 0], ['l', 'r', 'r', 0], ['l2', 'second', 'r', 10], ['l2', 'r', 'second', 0],
  ]);
});
