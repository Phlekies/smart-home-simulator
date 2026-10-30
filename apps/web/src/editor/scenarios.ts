import type { Project } from '../generated/project.ts';
import type { ScenarioAssumptions, ScenarioResult } from '../generated/scenario-result.ts';
import { stable } from './latestAnalysis.ts';
export type ScenarioRequest = { project: Project; scenarios: ScenarioAssumptions[]; engine: 'quick-estimate' };
export function automaticAssumptions(project: Project): Omit<ScenarioAssumptions, 'name'>[] {
  const doors = project.building.walls.filter(wall => wall.door === 'unknown').map(wall => wall.id);
  const materials = project.building.materials.filter(material => material.uncertainty).map(material => material.id);
  return [{ id: 'nominal', doors: {}, materials: {} },
    { id: 'best', doors: Object.fromEntries(doors.map(id => [id, 'open' as const])), materials: Object.fromEntries(materials.map(id => [id, 'low' as const])) },
    { id: 'worst', doors: Object.fromEntries(doors.map(id => [id, 'closed' as const])), materials: Object.fromEntries(materials.map(id => [id, 'high' as const])) }];
}
export function validateScenarios(result: ScenarioResult, request: ScenarioRequest) {
  const expected = [...automaticAssumptions(request.project), ...request.scenarios.map(({ name: _name, ...scenario }) => scenario)];
  if (result.engine !== request.engine || stable(result.scenarios.map(({ name: _name, ...scenario }) => scenario)) !== stable(expected)
    || stable(result.links.map(link => link.id).sort()) !== stable(request.project.links.map(link => link.id).sort())) throw new Error('Los escenarios recibidos pertenecen a otras hipótesis o enlaces.');
  for (const link of result.links) {
    const configured = request.project.links.find(item => item.id === link.id)!;
    if (link.hypotheses.some(id => !request.project.building.walls.some(wall => wall.id === id))) throw new Error('Las hipótesis contienen paredes ajenas al proyecto.');
    if (!link.outcomes.length && link.forward_range_dbm === null && link.reverse_range_dbm === null) {
      if (link.margin_sign !== 'incomplete') throw new Error('Un enlace sin datos no puede declarar un signo de margen consistente.');
      continue;
    }
    if (stable(link.outcomes.map(outcome => outcome.scenario_id)) !== stable(expected.map(scenario => scenario.id))) throw new Error('Faltan resultados de uno o más escenarios.');
    for (const outcome of link.outcomes) {
      if ((outcome.forward?.margin_db == null || outcome.reverse?.margin_db == null) && link.margin_sign !== 'incomplete') throw new Error('Faltan márgenes para comparar el signo entre escenarios.');
      if ((outcome.forward && (outcome.forward.tx_device_id !== configured.source_device_id || outcome.forward.rx_device_id !== configured.target_device_id))
        || (outcome.reverse && (outcome.reverse.tx_device_id !== configured.target_device_id || outcome.reverse.rx_device_id !== configured.source_device_id))) throw new Error('Un sentido recibido no corresponde a su enlace.');
    }
    for (const range of [link.forward_range_dbm, link.reverse_range_dbm]) {
      if (range && (range.length !== 2 || !range.every(Number.isFinite) || range[0] > range[1])) throw new Error('El rango de potencia recibido no es válido.');
    }
  }
}
export const scenarioNames: Record<string, string> = { nominal: 'Nominal', best: 'Mejor caso', worst: 'Peor caso' };
export const marginSignNames = { consistent: 'El signo del margen limitante se mantiene entre escenarios.',
  'depends-on-hypotheses': 'El signo del margen limitante cambia con las hipótesis.', incomplete: 'Datos incompletos para comparar el signo del margen limitante.' };
