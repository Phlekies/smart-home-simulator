import type { CoverageMapJob, CoverageMapResult } from '../generated/coverage-map.ts';
import type { CoverageRequest } from './coverage.ts';
import { genericRadio } from './connections.ts';

// Synthetic contract/race fixtures; never imported by the application UI.
export function coverageFixture(): { request: CoverageRequest; result: CoverageMapResult; queued: CoverageMapJob; done: CoverageMapJob } {
  const request: CoverageRequest = { project: { format: 'smart-environment-simulator', version: 1, units: 'm', name: 'Synthetic fixture',
    building: { width_m: 10, depth_m: 10, walls: [], materials: [{ id: 'm', name: 'Synthetic', loss_db_24ghz: 3, loss_db_5ghz: 5,
      extra_loss_db_per_cm: 0, evidence: 'Test only' }] },
    devices: [{ id: 'ap', name: 'AP', role: 'access-point', position: { x: 0, y: 0, z: 1.4 }, radios: [genericRadio('r')], evidence: 'Test only' }],
    links: [], settings: { path_loss_exponent: 2.1, system_gain_db: 0, extra_loss_db_per_m: 0 }, migration_notes: [], legacy_source: null },
    engine: 'quick-estimate', access_point_device_id: 'ap', access_point_radio_id: 'r',
    profile: { id: 'profile', name: 'Test', evidence: 'Test only', radio: genericRadio('client') },
    grid: { origin_x_m: 2, origin_y_m: -3, width_m: 1.2, depth_m: .2, resolution_m: 1, height_m: 1.4 }, points: [] };
  const { project: _project, ...parameters } = structuredClone(request);
  const result: CoverageMapResult = { parameters, engine: 'quick-estimate', engine_version: 'test', request_hash: 'b'.repeat(64),
    input_hash: 'a'.repeat(64), metric: 'direct-path-received-power', frequency_hz: 2.412e9, compatibility: 'unverified',
    columns: 2, rows: 1, cells: { forward_dbm: [-70, null], reverse_dbm: [-80, null], forward_margin_db: [null, null],
      reverse_margin_db: [null, null], status: ['partial', 'not-computed'] }, points: [], computed_cells: 0, partial_cells: 1,
    not_computed_cells: 1, elapsed_ms: 1, scope: 'Synthetic test', limitations: ['Test only'], reasons: ['Unknown data'] };
  const queued: CoverageMapJob = { job_id: 'job', request_hash: result.request_hash, state: 'queued', progress: 0, result: null, error: null };
  return { request, result, queued, done: { ...queued, state: 'done', progress: 1, result } };
}
