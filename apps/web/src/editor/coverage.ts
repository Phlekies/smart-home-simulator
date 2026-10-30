import type { CoverageMapParameters, CoverageMapResult } from '../generated/coverage-map.ts';
import type { Project } from '../generated/project.ts';

export type CoverageRequest = CoverageMapParameters & { project: Project };
export type MapMetric = 'forward_dbm' | 'reverse_dbm' | 'forward_margin_db' | 'reverse_margin_db';
export type CoverageLayer = { result: CoverageMapResult; imageUrl: string; metric: MapMetric };
export const metricNames: Record<MapMetric, string> = { forward_dbm: 'Señal AP → perfil', reverse_dbm: 'Señal perfil → AP',
  forward_margin_db: 'Margen AP → perfil', reverse_margin_db: 'Margen perfil → AP' };

export function mapExtent(result: CoverageMapResult) {
  const grid = result.parameters.grid;
  return { x: grid.origin_x_m, y: grid.origin_y_m, width: grid.width_m, height: grid.depth_m,
    textureWidth: result.columns * grid.resolution_m, textureHeight: result.rows * grid.resolution_m };
}
export function rasterCellSize(columns: number, rows: number) {
  return Math.max(1, Math.min(6, Math.floor(24000 / Math.max(columns, rows))));
}
export function mapColor(value: number | null, metric: MapMetric): string {
  if (value === null || !Number.isFinite(value)) return '#737d80';
  const margin = metric.includes('margin'), min = margin ? -30 : -100, max = margin ? 40 : -30;
  const t = Math.max(0, Math.min(1, (value - min) / (max - min)));
  return `rgb(${Math.round(80 - 45 * t)}, ${Math.round(50 + 150 * t)}, ${Math.round(135 + 50 * t)})`;
}
function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    const object = value as Record<string, unknown>;
    return `{${Object.keys(object).sort().map(key => `${JSON.stringify(key)}:${stable(object[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}
export function validateMapResult(result: CoverageMapResult, request: CoverageRequest, expectedHash: string) {
  const { project: _project, ...parameters } = request;
  const size = result.columns * result.rows;
  if (result.request_hash !== expectedHash || stable(result.parameters) !== stable(parameters)) throw new Error('El mapa recibido pertenece a otros parámetros. Vuelve a calcular.');
  if (!Number.isInteger(result.columns) || !Number.isInteger(result.rows) || result.columns < 1 || result.rows < 1 || size > 40000
    || result.columns !== Math.max(1, Math.ceil(parameters.grid.width_m / parameters.grid.resolution_m - 1e-9))
    || result.rows !== Math.max(1, Math.ceil(parameters.grid.depth_m / parameters.grid.resolution_m - 1e-9))
    || [...Object.keys(metricNames), 'status'].some(name => {
      const values = result.cells[name as keyof typeof result.cells];
      return !Array.isArray(values) || values.length !== size;
    }) || result.points.length !== parameters.points.length) {
    throw new Error('El mapa recibido está incompleto o tiene dimensiones no válidas.');
  }
}
