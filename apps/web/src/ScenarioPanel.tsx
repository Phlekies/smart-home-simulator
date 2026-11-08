import { api } from './api';
import type { Project } from './generated/project';
import type { ScenarioResult } from './generated/scenario-result';
import { marginSignNames, scenarioNames, validateScenarios } from './editor/scenarios';
import type { ScenarioRequest } from './editor/scenarios';
import { useAnalysis } from './useAnalysis';
const value = (number: number | null | undefined) => number == null ? 'Sin datos' : number.toFixed(2);
const range = (values: number[] | null) => values ? `${value(values[0])} a ${value(values[1])} dBm` : 'Sin datos';
export default function ScenarioPanel({ project, revision, disabled, onValidate, onInspect }: {
  project: Project; revision: number; disabled: boolean; onValidate: () => boolean; onInspect: (wallId: string) => void;
}) {
  const analysis = useAnalysis<ScenarioResult>(revision), result = analysis.result;
  const unknownDoors = project.building.walls.filter(wall => wall.door === 'unknown');
  const materials = project.building.materials.filter(material => material.uncertainty);
  const wallName = (id: string) => `Pared ${project.building.walls.findIndex(wall => wall.id === id) + 1}`;
  function run() {
    if (disabled || !onValidate()) return;
    const request: ScenarioRequest = { project, scenarios: [], engine: 'quick-estimate' };
    analysis.run(request, (input, signal) => api<ScenarioResult>('/scenario-simulations', input, signal), validateScenarios);
  }
  return <section className="panel results-panel analysis-panel" aria-labelledby="scenarios-title" aria-busy={analysis.pending}>
    <span className="eyebrow">RIESGO E HIPÓTESIS · TRAYECTO DIRECTO</span><h2 id="scenarios-title">Compara puertas y materiales inciertos.</h2>
    <p className="helper">{unknownDoors.length} puertas de estado desconocido · {materials.length} materiales con rango. Nominal: desconocidas cerradas y pérdidas nominales. Mejor: desconocidas abiertas y pérdidas mínimas. Peor: desconocidas cerradas y pérdidas máximas. Las puertas declaradas abiertas/cerradas permanecen fijas.</p>
    {!unknownDoors.length && !materials.length && <p className="helper">No hay hipótesis inciertas declaradas. Los tres escenarios pueden coincidir. Edita una pared y su material para indicar lo desconocido.</p>}
    <div className="analysis-actions"><button type="button" className="primary" onClick={run} disabled={disabled || analysis.pending || !project.links.length}>Comparar escenarios</button>
      {analysis.pending && <button type="button" onClick={analysis.clear}>Descartar respuesta de escenarios</button>}</div>
    {analysis.error && <p role="alert" className="message error">{analysis.error}</p>}
    <p role="status">{analysis.pending ? 'Evaluando hipótesis…' : result ? 'Escenarios disponibles para esta instalación.' : 'Sin escenarios vigentes.'}</p>
    {result && <><div className="result-meta"><span>{result.links.length} enlaces · {result.elapsed_ms.toFixed(1)} ms</span><span title={result.input_hash}>Instalación {result.input_hash.slice(0, 10)}</span></div>
      <details className="limitations"><summary>Hipótesis de cada escenario</summary><ul>{result.scenarios.map(scenario => <li key={scenario.id}><strong>{scenarioNames[scenario.id] ?? scenario.name}</strong>: {scenario.name}
        <ul>{Object.entries(scenario.doors).map(([id, state]) => <li key={id}>{wallName(id)}: {state === 'open' ? 'abierta' : 'cerrada'}</li>)}
          {Object.entries(scenario.materials).map(([id, bound]) => <li key={id}>{project.building.materials.find(material => material.id === id)?.name}: {bound === 'low' ? 'pérdida mínima' : bound === 'high' ? 'pérdida máxima' : 'pérdida nominal'}</li>)}</ul></li>)}</ul></details>
      <div className="scenario-links">{result.links.map(link => {
        const configured = project.links.find(item => item.id === link.id)!;
        const source = project.devices.find(device => device.id === configured.source_device_id)!, target = project.devices.find(device => device.id === configured.target_device_id)!;
        return <article className="scenario-link" key={link.id}><h3>{source.name} ({configured.source_radio_id}) ↔ {target.name} ({configured.target_radio_id})</h3>
          <p>Ida: {range(link.forward_range_dbm)} · Vuelta: {range(link.reverse_range_dbm)}. Radio: {link.compatibility === 'unverified' ? 'sin verificar' : link.compatibility === 'incompatible' ? 'incompatible' : 'compatible bajo los parámetros declarados'}.</p>
          <p className="scenario-sign">{marginSignNames[link.margin_sign]} No es una clasificación de fiabilidad.</p>
          <div className="table-scroll"><table><caption>Ida {source.name}→{target.name}; vuelta {target.name}→{source.name}</caption><thead><tr><th>Escenario</th><th>Señal ida / vuelta · dBm</th><th>Margen ida / vuelta · dB</th></tr></thead><tbody>
            {link.outcomes.map(outcome => <tr key={outcome.scenario_id}><td>{scenarioNames[outcome.scenario_id] ?? outcome.scenario_id}</td><td>{value(outcome.forward?.received_power_dbm)} / {value(outcome.reverse?.received_power_dbm)}</td><td>{value(outcome.forward?.margin_db)} / {value(outcome.reverse?.margin_db)}</td></tr>)}
            {!link.outcomes.length && <tr><td colSpan={3}>Sin resultados para este enlace; revisa sus radios y los motivos.</td></tr>}
          </tbody></table></div>
          <p className="helper">Hipótesis señaladas por el motor en este trayecto:</p><ul>{link.hypotheses.map(id => { const wall = project.building.walls.find(item => item.id === id)!; const material = project.building.materials.find(item => item.id === wall.material_id)!;
            return <li key={id}><button type="button" onClick={() => onInspect(id)}>{wallName(id)}</button> · {wall.door === 'unknown' ? 'puerta desconocida · ' : ''}{material.name}{material.uncertainty ? ` · ${material.uncertainty.source}` : ''}</li>; })}
            {!link.hypotheses.length && <li>Sin paredes inciertas señaladas en el trayecto directo.</li>}</ul>
          {link.reasons.length > 0 && <ul className="helper">{link.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul>}
        </article>;
      })}</div>
      <details className="limitations"><summary>Alcance y límites del cálculo</summary><p>{result.scope}</p><ul>{result.limitations.map((limit, index) => <li key={index}>{limit}</li>)}</ul></details>
    </>}
    <p className="comparison-limit">Los rangos son límites de escenarios declarados, sin probabilidad asociada. No hay calibración experimental. No se varían orientación, ruido o interferencias; una puerta abierta omite su segmento, sin difracción. Resultados de sesión, sin exportación persistente de escenarios.</p>
  </section>;
}
