import assert from 'node:assert/strict';
import test from 'node:test';
import { withDoor, makeMaterialRange, validatedMaterialPatch } from './uncertainty.ts';
import { coverageFixture } from './coverageFixture.ts';
import { adoptHistory, editHistory, emptyHistory, undoHistory } from './history.ts';
import type { Project, Wall } from '../generated/project.ts';
const material = { id: 'm', name: 'Test', loss_db_24ghz: 3, loss_db_5ghz: 5, extra_loss_db_per_cm: 0, evidence: 'Test only' };
const wall: Wall = { id: 'door', start: { x: 1.125, y: 0, z: 0 }, end: { x: 1.125, y: 4, z: 0 }, material_id: 'm', thickness_m: .12, height_m: 2.6 };
test('door states preserve exact geometry and can revert to a normal wall', () => {
  for (const state of ['open', 'closed', 'unknown', null] as const) {
    const changed = withDoor(wall, state);
    assert.deepEqual({ ...changed, door: undefined }, { ...wall, door: undefined }); assert.equal(changed.door, state);
  }
  assert.equal(wall.door, undefined);
});
test('material ranges accept equal boundaries and zero without treating them as unknown', () => {
  const range = makeMaterialRange(material, ['0', '3', '5', '5'], ' Test source ');
  assert.equal(range.loss_db_24ghz_low, 0); assert.equal(range.source, 'Test source');
});
test('empty, non-finite, reversed, negative and non-containing ranges are rejected', () => {
  for (const values of [['', '4', '1', '6'], ['NaN', '4', '1', '6'], ['4', '2', '1', '6'], ['-1', '4', '1', '6'],
    ['4', '8', '1', '6'], ['0', '4', '1', '1001']]) assert.throws(() => makeMaterialRange(material, values, 'source'));
  assert.throws(() => makeMaterialRange(material, ['0', '4', '1', '6'], '  '));
  assert.throws(() => makeMaterialRange(material, ['0', '4', '1', '6'], 'a'.repeat(501)));
});
test('nominal edits must remain inside an active range; patches are detached', () => {
  const range = makeMaterialRange(material, ['0', '4', '1', '6'], 'source');
  assert.throws(() => validatedMaterialPatch({ ...material, uncertainty: range }, { loss_db_24ghz: 5 }));
  const patch = validatedMaterialPatch(material, { uncertainty: range }); range.source = 'changed';
  assert.equal(patch.uncertainty?.source, 'source');
  assert.deepEqual(validatedMaterialPatch({ ...material, uncertainty: range }, { uncertainty: null }), { uncertainty: null });
});
test('door and shared material ranges survive JSON/history, with each action undoable', () => {
  const project = coverageFixture().request.project; project.building.walls = [wall, { ...wall, id: 'second' }];
  let history = adoptHistory(emptyHistory<Project>(), project);
  history = editHistory(history, draft => { draft.building.walls[0] = withDoor(draft.building.walls[0], 'unknown'); });
  history = editHistory(history, draft => { draft.building.materials[0].uncertainty = makeMaterialRange(material, ['0', '4', '1', '6'], 'source'); });
  const reopened = JSON.parse(JSON.stringify(history.present)) as Project;
  assert.equal(reopened.building.walls[0].door, 'unknown'); assert.equal(reopened.building.walls[1].door, undefined);
  assert.equal(reopened.building.materials[0].uncertainty?.source, 'source');
  assert.equal(undoHistory(history).present?.building.materials[0].uncertainty, undefined);
  assert.equal(undoHistory(undoHistory(history)).present?.building.walls[0].door, undefined);
});
