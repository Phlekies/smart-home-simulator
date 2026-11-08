import type { CoverageMapResult } from '../generated/coverage-map.ts';
import type { ProjectFingerprint } from '../generated/project-fingerprint.ts';

// A saved map is the API result kept as a local file, never inside the exportable project (B-132).
export const MAX_SAVED_MAP_BYTES = 20_000_000;
const CELL_ARRAYS = ['forward_dbm', 'reverse_dbm', 'forward_margin_db', 'reverse_margin_db', 'status'] as const;

export function parseSavedMap(text: string): CoverageMapResult {
  let data: unknown;
  try { data = JSON.parse(text); } catch { throw new Error('El archivo no es JSON válido.'); }
  const map = data as Partial<CoverageMapResult> | null;
  if (!map || typeof map !== 'object' || map.metric !== 'direct-path-received-power' || typeof map.input_hash !== 'string'
    || typeof map.request_hash !== 'string' || typeof map.engine_version !== 'string' || !map.parameters || !map.cells
    || !Number.isInteger(map.columns) || !Number.isInteger(map.rows) || (map.columns ?? 0) < 1 || (map.rows ?? 0) < 1) {
    throw new Error('No es un mapa guardado de esta aplicación: faltan la huella del proyecto, la versión del motor o las celdas.');
  }
  const cells = map.columns! * map.rows!;
  if (CELL_ARRAYS.some(key => !Array.isArray(map.cells![key]) || map.cells![key].length !== cells) || !Array.isArray(map.points)) {
    throw new Error('Las celdas del mapa no coinciden con su rejilla: el archivo está incompleto o alterado.');
  }
  return map as CoverageMapResult;
}

/** Why a saved map no longer describes the project, or null while it is current. */
export function savedMapStaleness(map: CoverageMapResult, fingerprint: ProjectFingerprint): string | null {
  if (map.engine_version !== fingerprint.engine_version) {
    return `Se calculó con el motor ${map.engine_version}; el actual es ${fingerprint.engine_version}.`;
  }
  if (map.input_hash !== fingerprint.input_hash) return 'El proyecto ha cambiado desde que se calculó.';
  return null;
}

export const savedMapFileName = (map: CoverageMapResult) => `mapa-${map.request_hash.slice(0, 10)}.json`;
