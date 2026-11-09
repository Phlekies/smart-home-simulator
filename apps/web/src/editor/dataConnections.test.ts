import assert from 'node:assert/strict';
import test from 'node:test';
import type { Link, Project } from '../generated/project.ts';
import { genericRadio, withRemovedConnection, withRemovedRadio } from './connections.ts';
import { attachedDataLinks, clearDanglingDataConnections, showDataConnection, validatedDataConnection } from './dataConnections.ts';
import { adoptHistory, editHistory, emptyHistory, undoHistory } from './history.ts';

function project(): Project {
  const link = (id: string, source: string, target: string): Link => ({
    id, source_device_id: source, source_radio_id: 'r1', target_device_id: target, target_radio_id: 'r1',
  });
  return {
    format: 'smart-environment-simulator', version: 1, name: 'Synthetic backhaul fixture', units: 'm',
    building: { width_m: 10, depth_m: 10, walls: [], materials: [] },
    devices: ['ap', 'repeater', 'gateway', 'sensor'].map(id => ({
      id, name: id, role: id === 'ap' ? 'access-point' : 'endpoint', evidence: 'Test only',
      position: { x: 0, y: 0, z: 1.4 }, radios: [genericRadio('r1'), genericRadio('r2')],
    })),
    links: [link('first-hop', 'repeater', 'ap'), link('second-hop', 'repeater', 'gateway')],
    settings: { path_loss_exponent: 2, extra_loss_db_per_m: 0, system_gain_db: 0 },
    migration_notes: [], legacy_source: null,
  };
}

test('wireless connections require a link touching either side of this device', () => {
  const fixture = project();
  assert.deepEqual(attachedDataLinks(fixture, 'ap').map(link => link.id), ['first-hop']);
  assert.deepEqual(validatedDataConnection(fixture, 'ap', 'wireless', 'first-hop', '  Enlace declarado  '),
    { kind: 'wireless', link_id: 'first-hop', note: 'Enlace declarado' });
  for (const link of ['', 'foreign', 'second-hop']) {
    assert.throws(() => validatedDataConnection(fixture, 'ap', 'wireless', link, ''), /toque este equipo/);
  }
});

test('other connection kinds omit wireless references and distinguish undefined from unknown', () => {
  const fixture = project();
  assert.equal(validatedDataConnection(fixture, 'ap', '', 'first-hop', ''), null);
  assert.deepEqual(validatedDataConnection(fixture, 'ap', 'unknown', 'first-hop', '  '),
    { kind: 'unknown', link_id: null, note: null });
  assert.deepEqual(validatedDataConnection(fixture, 'ap', 'gateway', 'first-hop', ''),
    { kind: 'gateway', link_id: null, note: null });
  assert.throws(() => validatedDataConnection(fixture, 'ap', 'wired', '', 'x'.repeat(501)), /500/);
  assert.ok(showDataConnection(fixture.devices[0]));
  assert.ok(!showDataConnection(fixture.devices[3]));
});

test('removing a link, radio or device clears only affected paths and is recoverable in one undo', () => {
  const fixture = project();
  fixture.devices[0].data_connection = validatedDataConnection(fixture, 'ap', 'wireless', 'first-hop', 'Conservar nota');
  fixture.devices[1].data_connection = validatedDataConnection(fixture, 'repeater', 'wireless', 'second-hop', '');
  const removals = [
    (draft: Project) => Object.assign(draft, withRemovedConnection(draft, 'first-hop')),
    (draft: Project) => Object.assign(draft, withRemovedRadio(draft, 'ap', 'r1')),
    (draft: Project) => {
      draft.devices = draft.devices.filter(device => device.id !== 'repeater');
      draft.links = draft.links.filter(link => link.source_device_id !== 'repeater' && link.target_device_id !== 'repeater');
    },
  ];
  for (const remove of removals) {
    const state = adoptHistory(emptyHistory<Project>(), fixture);
    const edited = editHistory(state, draft => { remove(draft); clearDanglingDataConnections(draft); });
    assert.deepEqual(edited.present?.devices[0].data_connection, { kind: 'unknown', link_id: null, note: 'Conservar nota' });
    const repeater = edited.present?.devices.find(device => device.id === 'repeater');
    if (repeater) assert.deepEqual(repeater.data_connection, fixture.devices[1].data_connection);
    assert.deepEqual(undoHistory(edited).present, fixture);
  }
});
