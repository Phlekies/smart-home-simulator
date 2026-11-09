import assert from 'node:assert/strict';
import test from 'node:test';
import type { DifferenceResult, Direction, Term } from '../generated/link-difference.ts';
import type { ComparisonRow } from './comparison.ts';
import { formatDifference, isBlockedStatus, termLabels, validateLinkDifference } from './linkDifference.ts';

function fixture() {
  const rows: ComparisonRow[] = [
    { linkId: 'link', direction: 'forward', txName: 'Router', rxName: 'Sensor', txRadioId: 'router', rxRadioId: 'sensor',
      power: { base: -85, alternative: -79, delta: 6 }, margin: { base: -3, alternative: 3, delta: 6 },
      baseStatus: 'below-threshold', alternativeStatus: 'above-threshold' },
    { linkId: 'link', direction: 'reverse', txName: 'Sensor', rxName: 'Router', txRadioId: 'sensor', rxRadioId: 'router',
      power: { base: -80, alternative: -80, delta: 0 }, margin: { base: 0, alternative: 0, delta: 0 },
      baseStatus: 'below-threshold', alternativeStatus: 'above-threshold' },
  ];
  const expectation = { baseHash: 'a'.repeat(64), alternativeHash: 'b'.repeat(64), engineVersion: 'test', rows };
  const direction = (row: ComparisonRow, direction: Direction) => ({
    direction, base_dbm: row.power.base, alternative_dbm: row.power.alternative, change_db: row.power.delta,
    base_margin_db: row.margin.base, alternative_margin_db: row.margin.alternative,
    terms: (Object.keys(termLabels) as Term[]).map(term => ({
      term, base_db: term === 'walls' && direction === 'forward' ? -6 : 0, alternative_db: 0,
      change_db: term === 'walls' && direction === 'forward' ? 6 : 0,
    })),
    walls: direction === 'forward' ? [{ wall_id: 'w1', change: 'no-longer-crossed' as const, change_db: 6 }] : [],
    reason: null,
  });
  const response: DifferenceResult = {
    engine: 'quick-estimate', engine_version: 'test', base_hash: expectation.baseHash, alternative_hash: expectation.alternativeHash,
    elapsed_ms: 1, scope: 'Synthetic test only', limitations: [], unmatched_link_ids: [],
    links: [{ link_id: 'link', base_status: 'below-threshold', alternative_status: 'above-threshold',
      forward: direction(rows[0], 'forward'), reverse: direction(rows[1], 'reverse'), base_limiting_margin_db: -3,
      alternative_limiting_margin_db: 0, limiting_change_db: 3, residual_risks: [] }],
  };
  return { response, expectation };
}

test('checks the expected bidirectional result and preserves a numeric zero margin', () => {
  const { response, expectation } = fixture();
  validateLinkDifference(response, expectation);
  assert.equal(response.links[0].alternative_limiting_margin_db, 0);
  assert.equal(formatDifference(0), '0.0');
  assert.equal(formatDifference(null), 'Sin datos');
  assert.equal(formatDifference(-.01), '0.0');
  assert.equal(formatDifference(.01), '0.0');
});

test('rejects another input, model version, link identity, or direction', () => {
  const { response, expectation } = fixture();
  for (const mutate of [(r: DifferenceResult) => { r.base_hash = r.alternative_hash; },
    (r: DifferenceResult) => { r.engine_version = 'another version'; },
    (r: DifferenceResult) => { r.links[0].link_id = 'other link'; },
    (r: DifferenceResult) => { r.unmatched_link_ids = ['extra']; },
    (r: DifferenceResult) => { r.links[0].reverse.direction = 'forward'; }]) {
    const changed = structuredClone(response);
    mutate(changed);
    assert.throws(() => validateLinkDifference(changed, expectation));
  }
});

test('rejects an inconsistent budget or limiting margin', () => {
  const { response, expectation } = fixture();
  for (const mutate of [(r: DifferenceResult) => { r.links[0].forward.terms[0].change_db = 10; },
    (r: DifferenceResult) => { r.links[0].forward.terms[0].term = 'walls'; },
    (r: DifferenceResult) => { r.links[0].forward.change_db = 7; },
    (r: DifferenceResult) => { r.links[0].limiting_change_db = 6; }]) {
    const changed = structuredClone(response);
    mutate(changed);
    assert.throws(() => validateLinkDifference(changed, expectation));
  }
});

test('missing signal direction stays unknown and has no calculated terms', () => {
  const { response, expectation } = fixture();
  const missing = { base: null, alternative: null, delta: null };
  expectation.rows[1].power = missing;
  expectation.rows[1].margin = missing;
  const link = response.links[0];
  Object.assign(link.reverse, { base_dbm: null, alternative_dbm: null, change_db: null, base_margin_db: null,
    alternative_margin_db: null, terms: [], reason: 'Sin potencia declarada' });
  Object.assign(link, { base_limiting_margin_db: null, alternative_limiting_margin_db: null, limiting_change_db: null });
  validateLinkDifference(response, expectation);
  link.reverse.terms = link.forward.terms;
  assert.throws(() => validateLinkDifference(response, expectation));
});

test('incompatible and unsupported links use blocked estimator status even if API includes raw terms', () => {
  for (const status of ['unsupported', 'incompatible'] as const) {
    const { response, expectation } = fixture();
    const link = response.links[0];
    link.base_status = status;
    link.alternative_status = status;
    for (const row of expectation.rows) {
      row.baseStatus = status;
      row.alternativeStatus = status;
      row.power = row.margin = { base: null, alternative: null, delta: null };
    }
    validateLinkDifference(response, expectation);
    assert.equal(isBlockedStatus(status), true);
  }
});
