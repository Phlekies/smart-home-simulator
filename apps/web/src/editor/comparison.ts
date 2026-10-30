import type { Point, Project } from '../generated/project.ts';
import type { DirectionResult, SimulationResult } from '../generated/simulation-result.ts';

export type ComparisonBase = { project: Project; result: SimulationResult; capturedAt: string };
export type MetricComparison = { base: number | null; alternative: number | null; delta: number | null };
export type ComparisonRow = {
  linkId: string; direction: 'forward' | 'reverse'; txName: string; rxName: string;
  txRadioId: string; rxRadioId: string;
  power: MetricComparison; margin: MetricComparison;
  baseStatus: SimulationResult['links'][number]['status']; alternativeStatus: SimulationResult['links'][number]['status'];
};
export type PositionComparison = { kind: 'waiting' | 'blocked'; reason: string }
  | { kind: 'ready'; rows: ComparisonRow[] };

function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record).sort().map(key => `${JSON.stringify(key)}:${stable(record[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}
const byId = <T extends { id: string }>(items: T[]) => [...items].sort((a, b) => a.id.localeCompare(b.id));

// Keep every project setting except names/positions. Never compare a radio change as a placement improvement.
function configuration(project: Project) {
  const { name: _name, devices, building, links, ...rest } = project;
  return stable({ ...rest, building: { ...building, walls: byId(building.walls), materials: byId(building.materials) },
    devices: byId(devices).map(({ name: _name, position: _position, radios, ...device }) => ({ ...device, radios: byId(radios) })),
    links: byId(links) });
}
export function samePositionConfiguration(base: Project, alternative: Project): boolean {
  return configuration(base) === configuration(alternative);
}

export function captureComparison(project: Project, result: SimulationResult, capturedAt = new Date().toISOString()): ComparisonBase {
  return { project: structuredClone(project), result: structuredClone(result), capturedAt };
}

export function movedDevices(base: Project, alternative: Project): { id: string; name: string; from: Point; to: Point }[] {
  const originals = new Map(base.devices.map(device => [device.id, device]));
  return alternative.devices.flatMap(device => {
    const before = originals.get(device.id);
    if (!before || ['x', 'y', 'z'].every(axis => before.position[axis as keyof Point] === device.position[axis as keyof Point])) return [];
    return [{ id: device.id, name: device.name, from: { ...before.position }, to: { ...device.position } }];
  });
}

function coherent(project: Project, result: SimulationResult) {
  if (project.links.length === 0 || result.links.length !== project.links.length) return false;
  const results = new Map(result.links.map(link => [link.id, link]));
  if (results.size !== result.links.length) return false;
  return project.links.every(link => {
    const computed = results.get(link.id); if (!computed) return false;
    return (!computed.forward || (computed.forward.tx_device_id === link.source_device_id && computed.forward.rx_device_id === link.target_device_id))
      && (!computed.reverse || (computed.reverse.tx_device_id === link.target_device_id && computed.reverse.rx_device_id === link.source_device_id));
  });
}
const finite = (value: number | null | undefined) => typeof value === 'number' && Number.isFinite(value) ? value : null;
function metric(before: number | null | undefined, after: number | null | undefined): MetricComparison {
  const base = finite(before), alternative = finite(after);
  return { base, alternative, delta: base === null || alternative === null ? null : alternative - base };
}

export function comparePositions(base: ComparisonBase, project: Project, result: SimulationResult | null): PositionComparison {
  if (!result) return { kind: 'waiting', reason: 'Ejecuta una nueva estimación de la alternativa para comparar. La base se conserva.' };
  if (!samePositionConfiguration(base.project, project)) return { kind: 'blocked',
    reason: 'Han cambiado radios, paredes, equipos, enlaces u otras condiciones. Esta comparación admite solo cambios de posición o altura. Deshaz esos cambios o fija una nueva base.' };
  if (base.result.engine !== result.engine || base.result.engine_version !== result.engine_version) return { kind: 'blocked',
    reason: 'El motor o su versión han cambiado. Vuelve a calcular y fija una nueva base con el mismo motor.' };
  if (!coherent(base.project, base.result) || !coherent(project, result)) return { kind: 'blocked',
    reason: 'Los resultados no contienen los mismos enlaces y sentidos que los proyectos. Recalcula antes de comparar.' };
  if (movedDevices(base.project, project).length > 0 && base.result.input_hash === result.input_hash) return { kind: 'blocked',
    reason: 'Las posiciones han cambiado pero el resultado identifica el escenario base. Ejecuta una nueva estimación antes de comparar.' };
  const before = new Map(base.result.links.map(link => [link.id, link]));
  const after = new Map(result.links.map(link => [link.id, link]));
  const names = new Map(project.devices.map(device => [device.id, device.name]));
  const rows = project.links.flatMap(link => (['forward', 'reverse'] as const).map(direction => {
    const original = before.get(link.id)!, current = after.get(link.id)!;
    const a: DirectionResult | null = original[direction], b: DirectionResult | null = current[direction];
    const txId = direction === 'forward' ? link.source_device_id : link.target_device_id;
    const rxId = direction === 'forward' ? link.target_device_id : link.source_device_id;
    return { linkId: link.id, direction, txName: names.get(txId) ?? txId, rxName: names.get(rxId) ?? rxId,
      txRadioId: direction === 'forward' ? link.source_radio_id : link.target_radio_id,
      rxRadioId: direction === 'forward' ? link.target_radio_id : link.source_radio_id,
      power: metric(a?.received_power_dbm, b?.received_power_dbm), margin: metric(a?.margin_db, b?.margin_db),
      baseStatus: original.status, alternativeStatus: current.status };
  }));
  return { kind: 'ready', rows };
}
