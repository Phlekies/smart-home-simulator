import assert from 'node:assert/strict';
import test from 'node:test';
import type { Link, Project } from '../generated/project.ts';
import { adoptHistory, editHistory, emptyHistory, redoHistory, undoHistory } from './history.ts';
import { genericRadio, hasRadioConnection, linksUsingRadio, withAddedConnection, withAddedRadio, withRemovedConnection, withRemovedRadio } from './connections.ts';

const link = (id: string, source = 'a', sourceRadio = 'r1', target = 'b', targetRadio = 'r1'): Link => ({ id,
  source_device_id: source, source_radio_id: sourceRadio, target_device_id: target, target_radio_id: targetRadio });
function project(): Project {
  return { format: 'smart-environment-simulator', version: 1, name: 'Synthetic radio fixture', units: 'm',
    building: { width_m: 10, depth_m: 10, walls: [], materials: [{ id: 'm', name: 'Synthetic', loss_db_24ghz: 3,
      loss_db_5ghz: 5, extra_loss_db_per_cm: 0, evidence: 'Test only' }] },
    devices: ['a', 'b', 'c'].map((id, index) => ({ id, name: id, role: 'endpoint', evidence: 'Test only',
      position: { x: index, y: 0, z: 1.4 }, radios: [genericRadio('r1'), genericRadio('r2')] })),
    links: [link('ab'), link('ca', 'c', 'r2', 'a'), link('cb', 'c'), link('ac', 'a', 'r2', 'c')],
    settings: { path_loss_exponent: 2.1, extra_loss_db_per_m: 0, system_gain_db: 0 },
    migration_notes: ['Keep note'], legacy_source: { original: { untouched: true } } };
}

test('generic radios leave power, sensitivity, channel and protocol unknown and are detached', () => {
  const first = genericRadio('r'), second = genericRadio('r');
  assert.equal(first.protocol, 'unknown'); assert.equal(first.tx_power_dbm, null);
  assert.equal(first.sensitivity_dbm, null); assert.equal(first.channel, null);
  first.tx_power_dbm = 10; assert.equal(second.tx_power_dbm, null);
});

test('adding a radio preserves other devices, links, metadata and original input', () => {
  const p = project(), original = structuredClone(p), next = withAddedRadio(p, 'a', 'r3');
  assert.deepEqual(p, original); assert.equal(next.devices[0].radios.length, 3);
  assert.equal(next.devices[0].radios[2]?.id, 'r3');
  assert.deepEqual(next.devices.slice(1), p.devices.slice(1)); assert.deepEqual(next.links, p.links);
  assert.deepEqual(next.legacy_source, p.legacy_source); assert.deepEqual(next.migration_notes, p.migration_notes);
  next.devices[0].radios[0].tx_power_dbm = 20; assert.equal(p.devices[0].radios[0].tx_power_dbm, null);
});

test('radio identifiers are unique within their device, not globally', () => {
  let p = project(); p = withAddedRadio(p, 'a', 'r3'); p = withAddedRadio(p, 'b', 'r3');
  assert.throws(() => withAddedRadio(p, 'a', 'r3'), /ya existe/);
  assert.equal(p.devices[1].radios[2]?.id, 'r3');
  assert.throws(() => withAddedRadio(p, 'missing', 'r4'), /equipo/);
});

test('the one-to-eight radio constraint is respected without deleting the device', () => {
  let p = project(); for (let i = 3; i <= 8; i++) p = withAddedRadio(p, 'a', `r${i}`);
  assert.equal(p.devices[0].radios.length, 8); assert.throws(() => withAddedRadio(p, 'a', 'r9'), /8 radios/);
  for (let i = 8; i >= 2; i--) p = withRemovedRadio(p, 'a', `r${i}`);
  assert.equal(p.devices[0].radios.length, 1); assert.throws(() => withRemovedRadio(p, 'a', 'r1'), /al menos una/);
  assert.equal(p.devices.length, 3);
});

test('radio removal cascades both directions, scoped by device even if radio IDs repeat', () => {
  const p = project(), original = structuredClone(p);
  assert.deepEqual(linksUsingRadio(p, 'a', 'r1').map(l => l.id), ['ab', 'ca']);
  const next = withRemovedRadio(p, 'a', 'r1');
  assert.deepEqual(next.links.map(l => l.id), ['cb', 'ac']);
  assert.equal(next.devices[0].radios[0].id, 'r2'); assert.equal(next.devices[1].radios[0].id, 'r1');
  assert.deepEqual(p, original); assert.deepEqual(next.legacy_source, original.legacy_source);
});

test('undo and redo restore a removed radio with every associated link in one action', () => {
  const p = project(); const initial = adoptHistory(emptyHistory<Project>(), p);
  const next = withRemovedRadio(p, 'a', 'r1');
  const removed = editHistory(initial, draft => Object.assign(draft, next));
  assert.equal(removed.past.length, 1); assert.equal(removed.present?.links.length, 2);
  const restored = undoHistory(removed); assert.deepEqual(restored.present, p);
  assert.deepEqual(redoHistory(restored).present, next);
});

test('an added connection keeps the exact chosen source and target radios', () => {
  const p = project(), candidate = link('second-radio', 'a', 'r2', 'b', 'r2');
  const next = withAddedConnection(p, candidate); assert.deepEqual(next.links.at(-1), candidate);
  candidate.target_radio_id = 'mutated outside'; assert.equal(next.links.at(-1)?.target_radio_id, 'r2');
  assert.equal(p.links.length, 4);
});

test('duplicate and reversed radio pairs are rejected but distinct interface pairs are valid', () => {
  const p = project(); assert.equal(hasRadioConnection(p, link('x')), true);
  assert.equal(hasRadioConnection(p, link('x', 'b', 'r1', 'a', 'r1')), true);
  assert.throws(() => withAddedConnection(p, link('dup')), /ya están enlazadas/);
  assert.throws(() => withAddedConnection(p, link('rev', 'b', 'r1', 'a', 'r1')), /ya están enlazadas/);
  assert.equal(hasRadioConnection(p, link('other', 'a', 'r2', 'b', 'r1')), false);
  assert.equal(withAddedConnection(p, link('other', 'a', 'r2', 'b', 'r1')).links.length, 5);
});

test('self-links, absent devices/radios and duplicate link identifiers cannot create dangling references', () => {
  const p = project(), original = structuredClone(p);
  for (const candidate of [link('self', 'a', 'r1', 'a', 'r2'), link('unknown-device', 'missing'),
    link('unknown-source-radio', 'a', 'missing'), link('unknown-target-radio', 'a', 'r2', 'b', 'missing'),
    link('ab', 'a', 'r2', 'b', 'r2')]) assert.throws(() => withAddedConnection(p, candidate));
  assert.deepEqual(p, original); assert.throws(() => withRemovedRadio(p, 'a', 'missing'));
});

test('identifiers outside canonical length limits are rejected before adding data', () => {
  for (const id of ['', 'x'.repeat(121)]) {
    assert.throws(() => genericRadio(id));
    assert.throws(() => withAddedRadio(project(), 'a', id));
    assert.throws(() => withAddedConnection(project(), link(id, 'a', 'r2', 'b', 'r2')));
  }
});

test('the 512-link limit blocks addition and does not prevent removing a link', () => {
  const p = project(); p.links = Array.from({ length: 512 }, (_, index) => link(`l-${index}`));
  assert.throws(() => withAddedConnection(p, link('overflow', 'a', 'r2', 'b', 'r2')), /512 enlaces/);
  const smaller = withRemovedConnection(p, 'l-0'); assert.equal(smaller.links.length, 511);
  assert.equal(withAddedConnection(smaller, link('last-slot', 'a', 'r2', 'b', 'r2')).links.length, 512);
});

test('removing one connection preserves devices, radios and all other links', () => {
  const p = project(), next = withRemovedConnection(p, 'ca');
  assert.deepEqual(next.devices, p.devices); assert.deepEqual(next.links.map(l => l.id), ['ab', 'cb', 'ac']);
  assert.equal(p.links.length, 4); assert.throws(() => withRemovedConnection(p, 'missing'));
});
