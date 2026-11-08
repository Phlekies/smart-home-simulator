import assert from 'node:assert/strict';
import test from 'node:test';
import type { Project } from '../generated/project.ts';
import { genericRadio } from './connections.ts';
import { creationSteps } from './onboarding.ts';

function home(): Project {
  return { format: 'smart-environment-simulator', version: 1, units: 'm', name: 'Casa',
    building: { width_m: 12, depth_m: 10, materials: [{ id: 'm', name: 'Tabique', loss_db_24ghz: 3, loss_db_5ghz: 5, extra_loss_db_per_cm: 0, evidence: 'Test' }],
      walls: [0, 1, 2, 3].map(index => ({ id: `w${index}`, start: { x: 0, y: index, z: 0 }, end: { x: 1, y: index, z: 0 },
        height_m: 2.6, thickness_m: .12, material_id: 'm' })) },
    devices: [], links: [], settings: { path_loss_exponent: 2.1, extra_loss_db_per_m: 0, system_gain_db: 0 },
    migration_notes: [], legacy_source: null };
}

const done = (steps: ReturnType<typeof creationSteps>) => steps.filter(step => step.done).map(step => step.id);

test('a new project with only its outline has every step pending', () => {
  assert.deepEqual(done(creationSteps(home(), false, false)), []);
});

test('steps follow what the project actually contains', () => {
  const project = home();
  project.building.walls.push({ ...project.building.walls[0], id: 'inner' });
  project.devices.push({ id: 'ap', name: 'AP', role: 'access-point', position: { x: 1, y: 1, z: 2 }, radios: [genericRadio('r')], evidence: 'Test' },
    { id: 's', name: 'Sensor', role: 'endpoint', position: { x: 5, y: 5, z: 1 }, radios: [genericRadio('r')], evidence: 'Test' });
  project.links.push({ id: 'l', source_device_id: 's', source_radio_id: 'r', target_device_id: 'ap', target_radio_id: 'r' });
  let steps = creationSteps(project, false, false);
  assert.deepEqual(done(steps), ['walls', 'devices', 'links']);
  assert.match(steps.find(step => step.id === 'radios')!.detail, /2 radios enlazadas con datos sin indicar/);
  for (const device of project.devices) Object.assign(device.radios[0], { protocol: 'wifi', channel: 1, tx_power_dbm: 10, sensitivity_dbm: -82 });
  steps = creationSteps(project, true, true);
  assert.deepEqual(done(steps), ['walls', 'devices', 'radios', 'links', 'estimate', 'save']);
});
