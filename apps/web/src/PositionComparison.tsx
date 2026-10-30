import { useMemo } from 'react';
import { comparePositions, movedDevices } from './editor/comparison';
import type { ComparisonBase } from './editor/comparison';
import type { Point, Project } from './generated/project';
import type { SimulationResult } from './generated/simulation-result';

const value = (number: number | null) => number === null ? 'Sin datos' : number.toFixed(1);
const delta = (number: number | null) => number === null ? 'Sin datos' : `${number > 0 ? '+' : ''}${Math.abs(number) < .05 ? '0.0' : number.toFixed(1)}`;
const point = (p: Point) => `X ${p.x}, Y ${p.y}, altura ${p.z} m`;
const statuses = { 'above-threshold': 'Sobre umbral', 'below-threshold': 'Bajo umbral', incompatible: 'Incompatible', unverified: 'Sin verificar', unsupported: 'Fuera de alcance' };

export default function PositionComparison({ project, result, base, disabled, onCapture, onClear, onRestore }: {
  project: Project; result: SimulationResult | null; base: ComparisonBase | null; disabled: boolean;
  onCapture: () => void; onClear: () => void; onRestore: () => void;
}) {
  const comparison = useMemo(() => base ? comparePositions(base, project, result) : null, [base, project, result]);
  const moves = useMemo(() => base ? movedDevices(base.project, project) : [], [base, project]);
  return <section className="results-panel comparison-panel panel" aria-labelledby="comparison-title" aria-busy={disabled}>
    <div className="results-heading"><div><span className="eyebrow">COMPARAR UBICACIONES</span><h2 id="comparison-title">Antes y después de mover equipos.</h2></div>
      <div className="comparison-actions">
        <button disabled={disabled || !result || !project.links.length} onClick={onCapture}>{base ? 'Reemplazar instalación base' : 'Fijar instalación base'}</button>
        {base && <button disabled={disabled} onClick={onClear}>Quitar comparación</button>}
      </div>
    </div>
    <p className="helper">Calcula la instalación y fíjala como base. Mueve un equipo o cambia su altura y vuelve a estimar con las mismas radios, paredes y condiciones.</p>
    <p className="comparison-limit">Diferencias del estimador, sin calibración experimental. Más señal prevista no garantiza conexión, velocidad ni estabilidad. La base es de sesión y no se guarda en JSON.</p>
    {base ? <>
      <div className="result-meta"><span>Base: {base.project.name}</span><span>Fijada: <time dateTime={base.capturedAt}>{new Date(base.capturedAt).toLocaleString()}</time></span>
        <span title={base.result.input_hash}>Escenario base {base.result.input_hash.slice(0, 10)}</span>
        {result && <span title={result.input_hash}>Alternativa {result.input_hash.slice(0, 10)}</span>}
        <span>Motor base {base.result.engine} · {base.result.engine_version}</span></div>
      <p role="status" className="comparison-state">{comparison?.kind === 'ready'
        ? moves.length ? `${moves.length} ${moves.length === 1 ? 'equipo desplazado' : 'equipos desplazados'}. Comparación calculada en ambos sentidos.` : 'No hay cambios de posición respecto a la base.'
        : comparison?.reason}</p>
      {moves.length > 0 && <details className="comparison-moves"><summary>Ver posiciones base y alternativa · {moves.length} {moves.length === 1 ? 'equipo' : 'equipos'}</summary>
        <ul>{moves.map(move => <li key={move.id}><strong>{move.name}</strong>: {point(move.from)} → {point(move.to)}</li>)}</ul>
        <button disabled={disabled} onClick={onRestore}>Restaurar posiciones base</button>
      </details>}
      {comparison?.kind === 'ready' && <div className="table-scroll"><table>
        <caption className="sr-only">Comparación de señal y margen: instalación base y alternativa, en ambos sentidos</caption>
        <thead><tr><th scope="col">Sentido del enlace</th><th scope="col">Base · dBm</th><th scope="col">Alternativa · dBm</th>
          <th scope="col">Cambio · dB</th><th scope="col">Margen base / alternativa · dB</th><th scope="col">Evaluación base / alternativa</th></tr></thead>
        <tbody>{comparison.rows.map(row => <tr key={`${row.linkId}-${row.direction}`}><th scope="row">{row.txName} → {row.rxName}
          <small className="link-radio-pair">{row.txRadioId} → {row.rxRadioId}</small></th>
          <td>{value(row.power.base)}</td><td>{value(row.power.alternative)}</td><td>{delta(row.power.delta)}</td>
          <td>{value(row.margin.base)} / {value(row.margin.alternative)}</td><td>{statuses[row.baseStatus]} / {statuses[row.alternativeStatus]}</td></tr>)}</tbody>
      </table></div>}
      <details className="limitations"><summary>Límites conservados de la instalación base</summary><p>{base.result.scope}</p><ul>{base.result.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul></details>
    </> : <p className="comparison-state" role="status">{result ? 'Puedes fijar el cálculo actual como instalación base.' : 'Ejecuta la primera estimación para fijar una base.'}</p>}
  </section>;
}
