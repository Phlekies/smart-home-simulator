import type { CoverageMapResult } from '../generated/coverage-map.ts';
import type { Project } from '../generated/project.ts';
import { mapGridDimensions, metricNames } from './coverage.ts';
import type { MapMetric } from './coverage.ts';

export const MAX_SAVED_MAP_BYTES = 20_000_000;

const object = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === 'object' && !Array.isArray(value);
const text = (value: unknown, min: number, max = Infinity): value is string =>
  typeof value === 'string' && value.length >= min && value.length <= max;
const number = (value: unknown, min = -Infinity, max = Infinity): value is number =>
  typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max;
const nullableNumber = (value: unknown, min?: number, max?: number) => value === null || number(value, min, max);
const hash = (value: unknown) => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const identifiers = (value: unknown) => text(value, 1, 120);
const strings = (value: unknown) => Array.isArray(value) && value.every(item => typeof item === 'string');
const metrics = Object.keys(metricNames) as MapMetric[];

function onlyKeys(record: Record<string, unknown>, keys: readonly string[]) {
  return Object.keys(record).every(key => keys.includes(key));
}

function validProvenance(radio: Record<string, unknown>) {
  const { provenance } = radio;
  if (provenance == null) return true;
  const fields = ['tx_power_dbm', 'tx_gain_dbi', 'rx_gain_dbi', 'sensitivity_dbm', 'noise_figure_db', 'channel', 'protocol'];
  return object(provenance) && onlyKeys(provenance, fields) && Object.entries(provenance).every(([field, entry]) => {
    if (!object(entry) || !onlyKeys(entry, ['provenance', 'source']) || (entry.source !== null && !text(entry.source, 0, 500))) return false;
    const missing = radio[field] === null || (field === 'protocol' && radio[field] === 'unknown');
    if (entry.provenance === 'inferred') return true;
    if (entry.provenance === 'unknown') return missing;
    return !missing && ['declared', 'measured', 'standard-minimum'].includes(entry.provenance as string);
  });
}

function validRadio(radio: unknown) {
  const ranges = {
    frequency_hz: [0, 100e9], bandwidth_hz: [0, 1e9], tx_gain_dbi: [-100, 100], rx_gain_dbi: [-100, 100],
    noise_figure_db: [0, 60], orientation_deg: [-360, 360], beamwidth_deg: [0, 360], pattern_sharpness: [.5, 100],
    side_lobe_attenuation_db: [0, 100], polarization_deg: [-360, 360],
  };
  return object(radio) && onlyKeys(radio, ['id', 'protocol', 'antenna', 'provenance', 'channel', 'tx_power_dbm', 'sensitivity_dbm', ...Object.keys(ranges)])
    && identifiers(radio.id) && ['wifi', 'thread', 'zigbee', 'ble', 'zwave', 'unknown'].includes(radio.protocol as string)
    && ['omnidirectional', 'directional'].includes(radio.antenna as string)
    && Object.entries(ranges).every(([key, [min, max]]) => number(radio[key], min, max))
    && radio.frequency_hz !== 0 && radio.bandwidth_hz !== 0 && radio.beamwidth_deg !== 0
    && (radio.channel === null || (number(radio.channel, 0, 1000) && Number.isInteger(radio.channel)))
    && nullableNumber(radio.tx_power_dbm, -100, 100) && nullableNumber(radio.sensitivity_dbm, -200, 0) && validProvenance(radio);
}

function validScenario(value: unknown) {
  if (value == null) return true;
  return object(value) && onlyKeys(value, ['id', 'name', 'doors', 'materials'])
    && identifiers(value.id) && text(value.name, 1, 160)
    && object(value.doors) && Object.entries(value.doors).every(([id, state]) => identifiers(id) && (state === 'open' || state === 'closed'))
    && object(value.materials) && Object.entries(value.materials).every(([id, bound]) =>
      identifiers(id) && (bound === 'low' || bound === 'nominal' || bound === 'high'));
}

function readDimensions(parameters: unknown, engine: unknown) {
  if (!object(parameters) || !onlyKeys(parameters, ['access_point_device_id', 'access_point_radio_id', 'profile', 'grid', 'points', 'engine', 'scenario'])
    || !identifiers(parameters.access_point_device_id) || !identifiers(parameters.access_point_radio_id)
    || parameters.engine !== engine || !['quick-estimate', 'sionna-rt', 'ns-3'].includes(engine as string) || !validScenario(parameters.scenario)) return null;
  const { profile, grid, points } = parameters;
  if (!object(profile) || !onlyKeys(profile, ['id', 'name', 'evidence', 'radio']) || !identifiers(profile.id)
    || !text(profile.name, 1, 160) || !text(profile.evidence, 0) || !validRadio(profile.radio)) return null;
  if (!object(grid) || !onlyKeys(grid, ['origin_x_m', 'origin_y_m', 'width_m', 'depth_m', 'resolution_m', 'height_m'])
    || !number(grid.origin_x_m, -10000, 10000) || !number(grid.origin_y_m, -10000, 10000)
    || !number(grid.width_m, Number.MIN_VALUE, 2000) || !number(grid.depth_m, Number.MIN_VALUE, 2000)
    || grid.origin_x_m + grid.width_m > 10000 || grid.origin_y_m + grid.depth_m > 10000
    || !number(grid.resolution_m, .1, 5) || !number(grid.height_m, -1000, 1000)) return null;
  if (!Array.isArray(points) || points.length > 256 || !points.every(point =>
    object(point) && onlyKeys(point, ['x', 'y', 'z'])
    && number(point.x, -10000, 10000) && number(point.y, -10000, 10000) && number(point.z, -1000, 1000))) return null;
  return { ...mapGridDimensions({ width_m: grid.width_m, depth_m: grid.depth_m, resolution_m: grid.resolution_m }), pointCount: points.length };
}

function validSample(status: unknown, values: unknown[]) {
  if (!values.every(value => nullableNumber(value))) return false;
  if (status === 'computed') return values.every(value => value !== null);
  if (status === 'partial') return values.some(value => value === null);
  return status === 'not-computed' && values.every(value => value === null);
}

function validCells(result: Record<string, unknown>, size: number) {
  const { cells } = result;
  if (!object(cells) || !Array.isArray(cells.status) || cells.status.length !== size) return false;
  const arrays = metrics.map(metric => cells[metric]);
  if (!arrays.every((array): array is unknown[] => Array.isArray(array) && array.length === size)) return false;
  const counts = { computed: 0, partial: 0, 'not-computed': 0 };
  for (let i = 0; i < size; i += 1) {
    const status = cells.status[i] as keyof typeof counts;
    if (!validSample(status, arrays.map(values => values[i]))) return false;
    counts[status] += 1;
  }
  return result.computed_cells === counts.computed && result.partial_cells === counts.partial
    && result.not_computed_cells === counts['not-computed'];
}

export function parseSavedMap(json: string): CoverageMapResult {
  let result: unknown;
  try { result = JSON.parse(json); }
  catch { throw new Error('El archivo no contiene JSON válido.'); }

  if (!object(result) || !hash(result.input_hash) || !hash(result.request_hash) || !text(result.engine_version, 1, 120)
    || result.metric !== 'direct-path-received-power' || !number(result.frequency_hz, Number.MIN_VALUE, 100e9)
    || (result.compatibility !== 'radio-compatible' && result.compatibility !== 'unverified')
    || !number(result.elapsed_ms, 0) || !text(result.scope, 0) || !strings(result.limitations) || !strings(result.reasons)) {
    throw new Error('El archivo no contiene un mapa de cobertura válido.');
  }
  const dimensions = readDimensions(result.parameters, result.engine);
  if (!dimensions) throw new Error('Los parámetros del mapa guardado son inválidos.');
  const { columns, rows, pointCount } = dimensions;
  if (columns !== result.columns || rows !== result.rows || columns * rows > 40_000 || !validCells(result, columns * rows)) {
    throw new Error('Las dimensiones, las celdas o sus recuentos son inválidos.');
  }
  if (!Array.isArray(result.points) || result.points.length !== pointCount || !result.points.every(point =>
    object(point) && (point.reason === null || text(point.reason, 0)) && validSample(point.status, metrics.map(metric => point[metric])))) {
    throw new Error('Los puntos exactos del mapa guardado son inválidos.');
  }
  return result as unknown as CoverageMapResult;
}

export const savedMapFileName = (map: CoverageMapResult) => `mapa-${map.request_hash.slice(0, 10)}.json`;

export function savedMapMismatch(result: CoverageMapResult, fingerprint: unknown, project: Project): string | null {
  if (!object(fingerprint) || fingerprint.engine !== 'quick-estimate'
    || !hash(fingerprint.input_hash) || !text(fingerprint.engine_version, 1, 120)) {
    throw new Error('La API local no devolvió una huella de proyecto válida.');
  }
  const anotherProject = fingerprint.input_hash !== result.input_hash;
  const anotherEngine = fingerprint.engine !== result.engine || fingerprint.engine_version !== result.engine_version;
  if (anotherProject && anotherEngine) return 'No coinciden la instalación y la versión del motor.';
  if (anotherProject) return 'La huella de la instalación es distinta.';
  if (anotherEngine) return 'La versión del motor es distinta.';

  const { access_point_device_id, access_point_radio_id } = result.parameters;
  const device = project.devices.find(item => item.id === access_point_device_id);
  if (device?.radios.find(item => item.id === access_point_radio_id)?.frequency_hz !== result.frequency_hz) {
    throw new Error('La radio emisora del archivo no coincide con la del proyecto.');
  }
  return null;
}
