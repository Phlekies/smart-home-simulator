import type { ComparisonRow } from './comparison.ts';
import type { DifferenceResult, DirectionDifference, Term, WallChange } from '../generated/link-difference.ts';

export const termLabels: Record<Term, string> = {
  tx_power: 'Potencia de transmisión',
  tx_antenna_gain: 'Ganancia de la antena emisora',
  rx_antenna_gain: 'Ganancia de la antena receptora',
  system_gain: 'Ganancia del sistema',
  path_loss: 'Pérdida con la distancia',
  walls: 'Pérdida en paredes',
  extra_loss: 'Pérdida adicional por distancia',
  polarization: 'Pérdida por polarización',
};

export const wallLabels: Record<WallChange['change'], string> = {
  'no-longer-crossed': 'deja de atravesarse',
  'newly-crossed': 'pasa a atravesarse',
  'loss-changed': 'cambia su pérdida',
};

export function isBlockedStatus(status: string) {
  return status === 'unsupported' || status === 'incompatible';
}

export function formatDifference(value: number | null) {
  if (value === null) return 'Sin datos';
  if (Math.abs(value) < .05) return '0.0';
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}`;
}

type DifferenceExpectation = {
  baseHash: string; alternativeHash: string; engineVersion: string; rows: ComparisonRow[];
};

const equal = (left: number | null, right: number | null) =>
  left === null || right === null ? left === right : Math.abs(left - right) <= 1e-6;
const difference = (base: number | null, alternative: number | null) =>
  base === null || alternative === null ? null : alternative - base;
const limiting = (forward: number | null, reverse: number | null) =>
  forward === null || reverse === null ? null : Math.min(forward, reverse);

function directionMatches(details: DirectionDifference, row: ComparisonRow) {
  if (details.direction !== row.direction) return false;
  // The difference API can return a raw budget even where the estimator blocks the link.
  if (isBlockedStatus(row.baseStatus) || isBlockedStatus(row.alternativeStatus)) return true;
  if (!equal(details.base_dbm, row.power.base) || !equal(details.alternative_dbm, row.power.alternative)
    || !equal(details.change_db, row.power.delta) || !equal(details.base_margin_db, row.margin.base)
    || !equal(details.alternative_margin_db, row.margin.alternative)) return false;
  if (row.power.delta === null) return details.terms.length === 0 && details.walls.length === 0;
  const terms = new Set(details.terms.map(term => term.term));
  return terms.size === details.terms.length && terms.size === Object.keys(termLabels).length
    && Object.keys(termLabels).every(term => terms.has(term as Term))
    && details.terms.every(term => Number.isFinite(term.base_db) && Number.isFinite(term.alternative_db)
      && equal(term.change_db, term.alternative_db - term.base_db))
    && equal(details.terms.reduce((sum, term) => sum + term.change_db, 0), row.power.delta)
    && details.walls.every(wall => Object.hasOwn(wallLabels, wall.change) && Number.isFinite(wall.change_db));
}

export function validateLinkDifference(response: DifferenceResult, expectation: DifferenceExpectation) {
  if (response.engine !== 'quick-estimate' || response.engine_version !== expectation.engineVersion
    || response.base_hash !== expectation.baseHash || response.alternative_hash !== expectation.alternativeHash) {
    throw new Error('El detalle corresponde a otro cálculo. Vuelve a estimar y comprueba la instalación base.');
  }
  const expectedRows = new Map(expectation.rows.filter(row => row.direction === 'forward').map(row => [row.linkId, row]));
  const expectedReverse = new Map(expectation.rows.filter(row => row.direction === 'reverse').map(row => [row.linkId, row]));
  const ids = new Set(response.links.map(link => link.link_id));
  if (response.unmatched_link_ids.length || ids.size !== response.links.length || ids.size !== expectedRows.size) {
    throw new Error('El detalle no contiene los mismos enlaces que la comparación.');
  }
  for (const link of response.links) {
    const forward = expectedRows.get(link.link_id), reverse = expectedReverse.get(link.link_id);
    if (!forward || !reverse || link.base_status !== forward.baseStatus || link.alternative_status !== forward.alternativeStatus
      || !directionMatches(link.forward, forward) || !directionMatches(link.reverse, reverse)) {
      throw new Error('El detalle no coincide con los sentidos o valores de la comparación.');
    }
    if (isBlockedStatus(link.base_status) || isBlockedStatus(link.alternative_status)) continue;
    const base = limiting(forward.margin.base, reverse.margin.base), alternative = limiting(forward.margin.alternative, reverse.margin.alternative);
    if (!equal(link.base_limiting_margin_db, base) || !equal(link.alternative_limiting_margin_db, alternative)
      || !equal(link.limiting_change_db, difference(base, alternative))) {
      throw new Error('El margen limitante recibido no coincide con los márgenes de ambos sentidos.');
    }
  }
}
