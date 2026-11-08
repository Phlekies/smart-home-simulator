import type { Project, Point } from '../generated/project.ts';
import type { CandidateEvaluation, PlacementCandidate, PlacementSearchParameters, PlacementSearchResult, PlacementZone } from '../generated/placement-search.ts';
import { stable } from './latestAnalysis.ts';
import { sameSimulationProject } from './referencePersistence.ts';
export type PlacementRequest = PlacementSearchParameters & { project: Project };
export function linkedPlacementTargets(project: Project, deviceId: string, radioId: string) {
  return project.links.flatMap(link => link.source_device_id === deviceId && link.source_radio_id === radioId
    ? [{ linkId: link.id, deviceId: link.target_device_id }] : link.target_device_id === deviceId && link.target_radio_id === radioId
      ? [{ linkId: link.id, deviceId: link.source_device_id }] : []);
}
export function finiteInput(value: string, label: string, min: number, max: number): number {
  const number = Number(value);
  if (!value.trim() || !Number.isFinite(number) || number < min || number > max) throw new Error(`${label}: introduce un número entre ${min} y ${max}.`);
  return number;
}
export function allowedPoint(id: string, label: string, coordinates: string[]): PlacementCandidate {
  if (!label.trim() || label.trim().length > 160) throw new Error('Etiqueta el lugar permitido con 1–160 caracteres.');
  const [x, y, z] = coordinates.map((value, index) => finiteInput(value, ['X', 'Y', 'Altura'][index], index === 2 ? -1000 : -10000, index === 2 ? 1000 : 10000));
  if (coordinates.length !== 3) throw new Error('El lugar necesita X, Y y altura.');
  return { id, label: label.trim(), position: { x, y, z } };
}
export function allowedZone(id: string, label: string, coordinates: string[]): PlacementZone {
  if (!label.trim() || label.trim().length > 160 || coordinates.length !== 6) throw new Error('Etiqueta la zona y completa sus seis parámetros.');
  const values = coordinates.map((value, index) => finiteInput(value, ['X mínimo', 'Y mínimo', 'X máximo', 'Y máximo', 'Altura', 'Paso'][index],
    index === 5 ? .25 : index === 4 ? -1000 : -10000, index === 5 ? 10 : index === 4 ? 1000 : 10000));
  const [min_x_m, min_y_m, max_x_m, max_y_m, height_m, step_m] = values;
  if (max_x_m < min_x_m || max_y_m < min_y_m) throw new Error('Los máximos de la zona deben ser iguales o mayores que los mínimos.');
  const zone = { id, label: label.trim(), min_x_m, min_y_m, max_x_m, max_y_m, height_m, step_m };
  if (zoneCount(zone) > 2000) throw new Error('La zona supera 2000 posiciones. Aumenta el paso o reduce su extensión.');
  return zone;
}
export function zoneCount(zone: PlacementZone): number {
  return (Math.floor((zone.max_x_m - zone.min_x_m) / zone.step_m + 1e-9) + 1) * (Math.floor((zone.max_y_m - zone.min_y_m) / zone.step_m + 1e-9) + 1);
}
export function validatePlacementRequest(request: PlacementRequest) {
  const ap = request.project.devices.find(device => device.id === request.access_point_device_id);
  if (!ap?.radios.some(radio => radio.id === request.access_point_radio_id)) throw new Error('Elige una radio del AP disponible.');
  const all = linkedPlacementTargets(request.project, ap.id, request.access_point_radio_id);
  const targets = all.filter(target => !request.target_device_ids.length || request.target_device_ids.includes(target.deviceId));
  if (!targets.length || request.target_device_ids.some(id => !all.some(target => target.deviceId === id))) throw new Error('Los equipos prioritarios necesitan enlaces con la radio del AP elegida.');
  const ids = [...request.candidates, ...request.zones].map(item => item.id);
  const count = request.candidates.length + request.zones.reduce((sum, zone) => sum + zoneCount(zone), 0);
  if (new Set(ids).size !== ids.length || ids.includes('current')) throw new Error('Los lugares necesitan identificadores únicos.');
  if (!count || count > 2000 || request.zones.length > 32 || (count + 1) * targets.length * Math.max(1, request.project.building.walls.length) > 2000000) {
    throw new Error('Revisa los límites: 1–2000 lugares, hasta 32 zonas y 2 millones de evaluaciones lugar×enlace×pared.');
  }
  return count;
}
function inAllowedPlace(row: CandidateEvaluation, request: PlacementRequest) {
  if (row.source === 'candidate') return request.candidates.some(candidate => candidate.id === row.candidate_id && stable(candidate.position) === stable(row.position));
  if (row.source !== 'zone') return false;
  return request.zones.some(zone => {
    const { x, y, z } = row.position;
    const onGrid = (value: number, min: number) => Math.abs((value - min) / zone.step_m - Math.round((value - min) / zone.step_m)) < 1e-7;
    return row.candidate_id.startsWith(`${zone.id}@`) && x >= zone.min_x_m && x <= zone.max_x_m + 1e-8 && y >= zone.min_y_m && y <= zone.max_y_m + 1e-8
      && z === zone.height_m && onGrid(x, zone.min_x_m) && onGrid(y, zone.min_y_m);
  });
}
export function validatePlacementResult(result: PlacementSearchResult, request: PlacementRequest) {
  const { project, ...parameters } = request;
  const ap = project.devices.find(device => device.id === parameters.access_point_device_id)!;
  if (stable(result.parameters) !== stable(parameters) || result.engine !== request.engine
    || result.access_point_device_id !== ap.id || result.access_point_radio_id !== parameters.access_point_radio_id
    || result.baseline.candidate_id !== 'current' || stable(result.baseline.position) !== stable(ap.position)
    || result.ranking.length > 50 || new Set(result.ranking.map(row => row.candidate_id)).size !== result.ranking.length
    || result.ranking.some(row => !inAllowedPlace(row, request))) throw new Error('La búsqueda recibida no corresponde a los lugares o parámetros solicitados.');
  const targets = linkedPlacementTargets(project, ap.id, parameters.access_point_radio_id).filter(target => !parameters.target_device_ids.length || parameters.target_device_ids.includes(target.deviceId));
  const expected = targets.map(target => `${target.linkId}\0${target.deviceId}`).sort();
  for (const row of [result.baseline, ...result.ranking]) {
    if (stable(row.targets.map(target => `${target.link_id}\0${target.device_id}`).sort()) !== stable(expected)) throw new Error('La respuesta contiene otros enlaces prioritarios.');
  }
}
export function comparablePlacementDelta(base: CandidateEvaluation, alternative: CandidateEvaluation): number | null {
  const keys = (row: CandidateEvaluation) => row.targets.filter(target => target.status === 'complete').map(target => `${target.link_id}\0${target.device_id}`).sort();
  return stable(keys(base)) === stable(keys(alternative)) ? alternative.delta_worst_margin_db : null;
}
export function placementToApply(project: Project, request: PlacementRequest, result: PlacementSearchResult, candidateId: string): Point {
  if (!sameSimulationProject(project, request.project)) throw new Error('La instalación cambió. Busca de nuevo antes de aplicar una alternativa.');
  validatePlacementResult(result, request);
  const candidate = result.ranking.find(row => row.candidate_id === candidateId);
  if (!candidate) throw new Error('La alternativa ya no está disponible.');
  return { ...candidate.position };
}
