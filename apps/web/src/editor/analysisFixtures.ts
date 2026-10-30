import { coverageFixture } from './coverageFixture.ts';
import { genericRadio } from './connections.ts';
import type { CandidateEvaluation, PlacementSearchResult } from '../generated/placement-search.ts';
import type { DirectionResult, ScenarioResult } from '../generated/scenario-result.ts';
import { automaticAssumptions } from './scenarios.ts';
import type { PlacementRequest } from './placement.ts';
import type { ScenarioRequest } from './scenarios.ts';
// Synthetic UI/contract test vectors only. No predictions or measurements.
export function analysisFixture() {
  const project = coverageFixture().request.project;
  project.devices[0].radios[0] = { ...project.devices[0].radios[0], protocol: 'wifi', tx_power_dbm: 20, sensitivity_dbm: -90 };
  for (const [index, id] of ['a', 'b'].entries()) {
    project.devices.push({ id, name: id, role: 'endpoint', position: { x: 2 + index * 4, y: 1, z: 1.4 }, evidence: 'Test only',
      radios: [{ ...genericRadio('client'), protocol: 'wifi', tx_power_dbm: 0, sensitivity_dbm: -80 }] });
    project.links.push({ id: `link-${id}`, source_device_id: 'ap', source_radio_id: 'r', target_device_id: id, target_radio_id: 'client' });
  }
  const request: PlacementRequest = { project, access_point_device_id: 'ap', access_point_radio_id: 'r', target_device_ids: [],
    candidates: [{ id: 'place', label: 'Allowed', position: { x: 3.125, y: 1.25, z: 2.375 } }], zones: [], engine: 'quick-estimate' };
  const targets = (reverse: number) => ['a', 'b'].map(id => ({ device_id: id, link_id: `link-${id}`, forward_margin_db: 5,
    reverse_margin_db: reverse, limiting_margin_db: reverse, limiting_direction: 'reverse' as const, status: 'complete' as const, reason: null }));
  const baseline: CandidateEvaluation = { candidate_id: 'current', label: 'Current', source: 'current', position: { ...project.devices[0].position },
    targets: targets(-2), complete_targets: 2, worst_margin_db: -2, mean_margin_db: -2, worst_target_id: 'a', delta_worst_margin_db: null };
  const { project: _project, ...parameters } = structuredClone(request);
  const result: PlacementSearchResult = { parameters, engine: 'quick-estimate', engine_version: 'test', input_hash: 'a'.repeat(64), request_hash: 'b'.repeat(64),
    access_point_device_id: 'ap', access_point_radio_id: 'r', criterion: 'max-min-bidirectional-margin', ranked: true, target_device_ids: ['a', 'b'],
    baseline, ranking: [{ ...structuredClone(baseline), candidate_id: 'place', label: 'Allowed', source: 'candidate',
      position: { ...request.candidates[0].position }, targets: targets(1), worst_margin_db: 1, mean_margin_db: 1, delta_worst_margin_db: 3 }],
    evaluated: 1, excluded: [], elapsed_ms: 1, scope: 'Test only', limitations: ['No field validation'], reasons: [] };
  const scenarioRequest: ScenarioRequest = { project, scenarios: [], engine: 'quick-estimate' };
  const direction = (tx: string, rx: string, power: number): DirectionResult => ({ tx_device_id: tx, rx_device_id: rx, received_power_dbm: power,
    margin_db: null, distance_m: 2, path_loss_db: 70, wall_loss_db: 0, crossed_wall_ids: [], noise_dbm: -90, snr_db: 20 });
  const scenarios = automaticAssumptions(project).map(scenario => ({ ...scenario, name: scenario.id }));
  const scenarioResult: ScenarioResult = { engine: 'quick-estimate', engine_version: 'test', input_hash: 'a'.repeat(64), scenarios,
    links: project.links.map(link => ({ id: link.id, compatibility: 'unverified', outcomes: scenarios.map((scenario, index) => ({ scenario_id: scenario.id,
      forward: direction(link.source_device_id, link.target_device_id, [-70, -60, -80][index]), reverse: null })),
      forward_range_dbm: [-80, -60], reverse_range_dbm: null, hypotheses: [], margin_sign: 'incomplete', reasons: ['Test missing return'] })),
    elapsed_ms: 1, scope: 'Test only', limitations: ['No field validation'] };
  return { project, request, result, scenarioRequest, scenarioResult };
}
