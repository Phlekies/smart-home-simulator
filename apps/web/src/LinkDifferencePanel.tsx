import { useRef, useState } from 'react';
import { api } from './api';
import type { ComparisonBase, ComparisonRow } from './editor/comparison';
import { formatDifference, isBlockedStatus, termLabels, validateLinkDifference, wallLabels } from './editor/linkDifference';
import type { DifferenceResult, DirectionDifference } from './generated/link-difference';
import type { Project } from './generated/project';
import type { SimulationResult } from './generated/simulation-result';
import { useAnalysis } from './useAnalysis';

const margin = (value: number | null) => value === null ? 'Sin datos' : `${value.toFixed(1)} dB`;

function DirectionTerms({ direction, label }: { direction: DirectionDifference; label: string }) {
  return <section>
    <h4>{label}</h4>
    {direction.reason && <p className="helper">{direction.reason}</p>}
    {direction.terms.length > 0 && <div className="table-scroll"><table>
      <caption className="sr-only">Contribuciones del modelo al cambio de potencia · {label}</caption>
      <thead><tr><th scope="col">Término</th><th scope="col">Base</th><th scope="col">Alternativa</th>
        <th scope="col">Cambio · dB</th></tr></thead>
      <tbody>{direction.terms.map(term => <tr key={term.term}>
        <th scope="row">{termLabels[term.term]} · {term.term === 'tx_power' ? 'dBm' : 'dB'}</th><td>{term.base_db.toFixed(1)}</td>
        <td>{term.alternative_db.toFixed(1)}</td><td>{formatDifference(term.change_db)}</td>
      </tr>)}</tbody>
    </table></div>}
    {direction.walls.length > 0 && <ul>{direction.walls.map(wall =>
      <li key={wall.wall_id}>Pared {wall.wall_id}: {wallLabels[wall.change]} ({formatDifference(wall.change_db)} dB).</li>)}</ul>}
  </section>;
}

export default function LinkDifferencePanel({ base, project, current, rows, disabled, onValidate }: {
  base: ComparisonBase; project: Project; current: SimulationResult; rows: ComparisonRow[]; disabled: boolean;
  onValidate?: () => boolean;
}) {
  // PositionComparison keys this panel by the base and alternative calculation identities.
  const analysis = useAnalysis<DifferenceResult>(0);
  const button = useRef<HTMLButtonElement>(null);
  const [selected, setSelected] = useState('');
  const result = analysis.result;
  const forward = rows.filter(row => row.direction === 'forward');
  const activeId = result?.links.some(link => link.link_id === selected) ? selected : result?.links[0]?.link_id ?? '';
  const detail = result?.links.find(link => link.link_id === activeId);
  const activeRow = forward.find(row => row.linkId === activeId);
  const blocked = detail && (isBlockedStatus(detail.base_status) || isBlockedStatus(detail.alternative_status));
  const reasons = detail ? new Set([
    ...(base.result.links.find(link => link.id === detail.link_id)?.reasons ?? []),
    ...(current.links.find(link => link.id === detail.link_id)?.reasons ?? []),
  ]) : new Set<string>();

  function explain() {
    if (disabled || analysis.pending || onValidate?.() === false) return;
    analysis.run({ base: base.project, alternative: project, engine: 'quick-estimate' as const },
      (request, signal) => api<DifferenceResult>('/link-differences', request, signal),
      response => validateLinkDifference(response, {
        baseHash: base.result.input_hash, alternativeHash: current.input_hash, engineVersion: current.engine_version, rows,
      }));
  }

  return <section aria-labelledby="difference-title">
    <h3 id="difference-title">Explicación del cambio de señal</h3>
    <p className="helper">Los términos describen la aritmética del modelo de trayecto directo con valores nominales. Las cifras están redondeadas. Los riesgos de la alternativa se muestran sin probabilidades.</p>
    <div className="comparison-actions">
      <button ref={button} disabled={disabled} aria-disabled={analysis.pending || undefined}
        onClick={explain}>Explicar cambios por enlace</button>
      {analysis.pending && <button onClick={() => { analysis.clear(); button.current?.focus(); }}>Cancelar explicación</button>}
    </div>
    <p role="status" className="comparison-state">{analysis.pending ? 'Calculando la explicación en la API local…'
      : result ? 'Explicación lista. Elige un enlace para ver ambos sentidos.' : ''}</p>
    {analysis.error && <p role="alert" className="message error">No se pudo obtener la explicación. {analysis.error}</p>}
    {result && detail && activeRow && <>
      <label className="field"><span>Enlace para ver el detalle</span>
        <select value={activeId} onChange={event => setSelected(event.target.value)}>
          {forward.map(row => <option key={row.linkId} value={row.linkId}>
            {row.txName} ({row.txRadioId}) ↔ {row.rxName} ({row.rxRadioId})
          </option>)}
        </select>
      </label>
      {blocked ? <>
        <p className="helper">Presupuesto no comparable. En al menos una versión las radios son incompatibles o quedan fuera del alcance del estimador.</p>
        {reasons.size > 0 && <ul>{[...reasons].map(reason => <li key={reason}>{reason}</li>)}</ul>}
      </> : <>
        <p>Margen limitante de ambos sentidos · Base {margin(detail.base_limiting_margin_db)} · Alternativa {margin(detail.alternative_limiting_margin_db)}
          {' · '}Cambio {detail.limiting_change_db === null ? 'Sin datos' : `${formatDifference(detail.limiting_change_db)} dB`}.</p>
        <DirectionTerms direction={detail.forward} label={`Ida · ${activeRow.txName} → ${activeRow.rxName}`} />
        <DirectionTerms direction={detail.reverse} label={`Vuelta · ${activeRow.rxName} → ${activeRow.txName}`} />
        <h4>Riesgos y datos pendientes de la alternativa</h4>
        {detail.residual_risks.length > 0 ? <ul>{detail.residual_risks.map((risk, index) => <li key={index}>{risk}</li>)}</ul>
          : <p className="helper">El modelo no ha señalado riesgos adicionales para este enlace. Sigue siendo una estimación.</p>}
      </>}
      <details className="limitations"><summary>Alcance y límites de la explicación</summary>
        <ul>{result.limitations.map((limit, index) => <li key={index}>{limit}</li>)}</ul>
      </details>
    </>}
  </section>;
}
