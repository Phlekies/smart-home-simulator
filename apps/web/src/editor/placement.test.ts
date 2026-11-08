import test from 'node:test';
import assert from 'node:assert/strict';
import { analysisFixture } from './analysisFixtures.ts';
import { allowedPoint, allowedZone, comparablePlacementDelta, linkedPlacementTargets, placementToApply, validatePlacementRequest, validatePlacementResult, zoneCount } from './placement.ts';
test('allowed points retain decimals and zones count samples without enumerating large arrays', () => {
  assert.deepEqual(allowedPoint('p', ' Exact ', ['-2.125', '3.75', '1.375']).position, { x: -2.125, y: 3.75, z: 1.375 });
  assert.equal(zoneCount(allowedZone('z', 'Zone', ['0', '0', '1.2', '.5', '1.4', '.5'])), 6);
  assert.throws(() => allowedZone('z', 'Too big', ['-10000', '-10000', '10000', '10000', '1.4', '.25']), /2000/);
});
test('invalid coordinates, labels, zone ordering and step never become permitted places', () => {
  for (const values of [['', '1', '1'], ['NaN', '1', '1'], ['10001', '1', '1'], ['0', '1', '-1001']]) assert.throws(() => allowedPoint('p', 'test', values));
  assert.throws(() => allowedPoint('p', ' ', ['0', '0', '1']));
  for (const values of [['2', '0', '1', '1', '1.4', '1'], ['0', '0', '1', '1', '1.4', '.24']]) assert.throws(() => allowedZone('z', 'test', values));
});
test('priority links are scoped to the selected AP radio in both directions', () => {
  const { project, request } = analysisFixture();
  project.links[0] = { ...project.links[0], source_device_id: 'a', source_radio_id: 'client', target_device_id: 'ap', target_radio_id: 'r' };
  assert.deepEqual(linkedPlacementTargets(project, 'ap', 'r').map(target => target.deviceId), ['a', 'b']);
  assert.deepEqual(linkedPlacementTargets(project, 'ap', 'other'), []);
  request.target_device_ids = ['foreign']; assert.throws(() => validatePlacementRequest(request));
});
test('candidate IDs, total positions, zone count and work limits are checked before HTTP', () => {
  const { request } = analysisFixture(); assert.equal(validatePlacementRequest(request), 1);
  request.candidates.push({ ...request.candidates[0] }); assert.throws(() => validatePlacementRequest(request)); request.candidates.pop();
  request.zones = [allowedZone('z', 'test', ['0', '0', '43', '43', '1.4', '1'])];
  request.project.building.walls = Array.from({ length: 600 }, (_, index) => ({ id: String(index), start: { x: 0, y: 0, z: 0 }, end: { x: 1, y: 0, z: 0 }, thickness_m: .1, height_m: 2.6, material_id: 'm' }));
  assert.throws(() => validatePlacementRequest(request), /límites/);
});
test('result parameters, links and allowed positions must match before any alternative is applied', () => {
  const { project, request, result } = analysisFixture(); validatePlacementResult(result, request);
  for (const mutate of [(r: typeof result) => { r.parameters.access_point_radio_id = 'other'; }, (r: typeof result) => { r.ranking[0].position.x = 999; },
    (r: typeof result) => { r.ranking[0].targets[0].link_id = 'foreign'; }, (r: typeof result) => { r.baseline.position.x = 99; }]) {
    const changed = structuredClone(result); mutate(changed); assert.throws(() => validatePlacementResult(changed, request));
  }
  const position = placementToApply(project, request, result, 'place'); position.x = 99; assert.equal(result.ranking[0].position.x, 3.125);
  const moved = structuredClone(project); moved.devices[1].position.x += .1; assert.throws(() => placementToApply(moved, request, result, 'place'));
});
test('zone results accept only points on the declared grid at its declared height', () => {
  const { request, result } = analysisFixture(); request.candidates = []; request.zones = [allowedZone('z', 'zone', ['0', '0', '1', '1', '1.4', '.5'])];
  const { project: _project, ...parameters } = structuredClone(request); result.parameters = parameters;
  Object.assign(result.ranking[0], { candidate_id: 'z@0.5,1', source: 'zone', position: { x: .5, y: 1, z: 1.4 } });
  validatePlacementResult(result, request); result.ranking[0].position.x = .6; assert.throws(() => validatePlacementResult(result, request));
});
test('a delta is suppressed when equal complete counts hide different complete links', () => {
  const { result } = analysisFixture(); assert.equal(comparablePlacementDelta(result.baseline, result.ranking[0]), 3);
  result.baseline.targets[0].status = 'incomplete'; result.ranking[0].targets[1].status = 'incomplete';
  assert.equal(comparablePlacementDelta(result.baseline, result.ranking[0]), null);
});
