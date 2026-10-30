import test from 'node:test';
import assert from 'node:assert/strict';
import { automaticAssumptions, validateScenarios } from './scenarios.ts';
import { analysisFixture } from './analysisFixtures.ts';
test('automatic hypotheses vary only unknown doors and materials with a declared range', () => {
  const { project } = analysisFixture();
  project.building.walls = ['unknown', 'open', 'closed'].map((door, index) => ({ id: String(index), door: door as 'unknown' | 'open' | 'closed',
    start: { x: 1, y: 0, z: 0 }, end: { x: 1, y: 4, z: 0 }, height_m: 2.6, thickness_m: .1, material_id: 'm' }));
  project.building.materials[0].uncertainty = { loss_db_24ghz_low: 1, loss_db_24ghz_high: 5, loss_db_5ghz_low: 1, loss_db_5ghz_high: 9, source: 'test' };
  const scenarios = automaticAssumptions(project); assert.deepEqual(scenarios[1].doors, { '0': 'open' }); assert.deepEqual(scenarios[2].doors, { '0': 'closed' });
  assert.deepEqual(scenarios[0].materials, {}); assert.deepEqual(scenarios[1].materials, { m: 'low' });
});
test('valid partial results retain absent return and unknown margins rather than inventing values', () => {
  const { scenarioRequest, scenarioResult } = analysisFixture(); validateScenarios(scenarioResult, scenarioRequest);
  assert.equal(scenarioResult.links[0].reverse_range_dbm, null); assert.equal(scenarioResult.links[0].outcomes[0].forward?.margin_db, null);
});
test('other assumptions, links, directions or omitted outcomes reject a scenario response', () => {
  const { scenarioRequest, scenarioResult } = analysisFixture();
  for (const mutate of [(r: typeof scenarioResult) => { r.scenarios[1].doors.foreign = 'open'; }, (r: typeof scenarioResult) => { r.links[0].id = 'foreign'; },
    (r: typeof scenarioResult) => { r.links[0].outcomes.pop(); }, (r: typeof scenarioResult) => { r.links[0].outcomes[0].forward!.tx_device_id = 'foreign'; }]) {
    const changed = structuredClone(scenarioResult); mutate(changed); assert.throws(() => validateScenarios(changed, scenarioRequest));
  }
});
test('noncomputed links can remain explicit while malformed ranges are rejected', () => {
  const { scenarioRequest, scenarioResult } = analysisFixture();
  for (const range of [[-60, -80], [NaN, -60], [-80]]) {
    const changed = structuredClone(scenarioResult); changed.links[0].forward_range_dbm = range;
    assert.throws(() => validateScenarios(changed, scenarioRequest));
  }
  const blocked = scenarioResult.links[0]; blocked.outcomes = []; blocked.forward_range_dbm = null;
  validateScenarios(scenarioResult, scenarioRequest);
});
test('incomplete budgets cannot be presented as a consistent margin sign', () => {
  const { scenarioRequest, scenarioResult } = analysisFixture(); scenarioResult.links[0].margin_sign = 'consistent';
  assert.throws(() => validateScenarios(scenarioResult, scenarioRequest), /márgenes/);
  scenarioResult.links[0].outcomes = []; scenarioResult.links[0].forward_range_dbm = null;
  assert.throws(() => validateScenarios(scenarioResult, scenarioRequest), /sin datos/);
});
