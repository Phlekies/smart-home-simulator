import { useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { api } from './api';
import type { Point, Project } from './generated/project';
import type { PlacementCandidate, PlacementSearchResult, PlacementZone } from './generated/placement-search';
import { allowedPoint, allowedZone, comparablePlacementDelta, linkedPlacementTargets, placementToApply, validatePlacementRequest, validatePlacementResult, zoneCount } from './editor/placement';
import type { PlacementRequest } from './editor/placement';
import { useAnalysis } from './useAnalysis';

const key = (device: string, radio: string) => JSON.stringify([device, radio]);
const number = (value: number | null, signed = false) => value === null ? 'Sin datos' : `${signed && value > 0 ? '+' : ''}${value.toFixed(2)}`;
const targetReason = (reason: string) => reason === 'missing-power-or-sensitivity' ? 'Falta potencia o sensibilidad' : reason === 'too-close' ? 'Separación inferior a 0,1 m' : reason;
export default function PlacementSearch({ project, revision, disabled, onValidate, onApply }: {
  project: Project; revision: number; disabled: boolean; onValidate: () => boolean; onApply: (deviceId: string, position: Point) => void;
}) {
  const first = project.devices.find(device => ['access-point', 'controller'].includes(device.role)) ?? project.devices[0];
  const options = project.devices.flatMap(device => device.radios.map(radio => ({ device, radio, key: key(device.id, radio.id) })));
  const [apKey, setAP] = useState(first ? key(first.id, first.radios[0].id) : '');
  const ap = options.find(option => option.key === apKey);
  const [priorities, setPriorities] = useState<string[]>([]), [points, setPoints] = useState<PlacementCandidate[]>([]), [zones, setZones] = useState<PlacementZone[]>([]);
  const [pointLabel, setPointLabel] = useState('Lugar permitido'), [pointFields, setPointFields] = useState([String(first?.position.x ?? 0), String(first?.position.y ?? 0), String(first?.position.z ?? 1.4)]);
  const [zoneLabel, setZoneLabel] = useState('Zona permitida'), [zoneFields, setZoneFields] = useState(['0', '0', String(project.building.width_m), String(project.building.depth_m), '1.4', '1']);
  const [confirmed, setConfirmed] = useState(false), [error, setError] = useState(''), [applied, setApplied] = useState(''), [selected, setSelected] = useState('');
  const analysis = useAnalysis<PlacementSearchResult>(revision), lastRequest = useRef<PlacementRequest | null>(null);
  const targetLinks = ap ? linkedPlacementTargets(project, ap.device.id, ap.radio.id) : [];
  const targetDevices = project.devices.filter(device => targetLinks.some(target => target.deviceId === device.id));
  const places = points.length + zones.reduce((sum, zone) => sum + zoneCount(zone), 0);
  function edit(action: () => void) { analysis.clear(); setError(''); setApplied(''); action(); }
  function addPoint(event: FormEvent) {
    event.preventDefault();
    try {
      const point = allowedPoint(crypto.randomUUID(), pointLabel, pointFields);
      if (places >= 2000) throw new Error('La búsqueda admite hasta 2000 posiciones.');
      edit(() => setPoints(previous => [...previous, point]));
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  function addZone(event: FormEvent) {
    event.preventDefault();
    try {
      const zone = allowedZone(crypto.randomUUID(), zoneLabel, zoneFields);
      if (zones.length >= 32 || places + zoneCount(zone) > 2000) throw new Error('La suma de lugares supera 2000 posiciones o 32 zonas.');
      edit(() => setZones(previous => [...previous, zone]));
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  function run() {
    if (disabled || !onValidate()) return;
    try {
      if (!ap) throw new Error('Elige la radio del AP que se movería.');
      if (!confirmed) throw new Error('Confirma que los lugares declarados permiten alimentación, cableado y montaje.');
      const request: PlacementRequest = { project, access_point_device_id: ap.device.id, access_point_radio_id: ap.radio.id,
        target_device_ids: priorities, candidates: points, zones, engine: 'quick-estimate' };
      validatePlacementRequest(request); lastRequest.current = structuredClone(request); setError(''); setApplied(''); setSelected('');
      analysis.run(request, (input, signal) => api<PlacementSearchResult>('/placement-searches', input, signal), validatePlacementResult);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  const result = analysis.result, alternative = result?.ranking.find(candidate => candidate.candidate_id === selected) ?? result?.ranking[0];
  function apply() {
    if (!result || !alternative || !lastRequest.current || disabled || !onValidate()) return;
    try {
      const position = placementToApply(project, lastRequest.current, result, alternative.candidate_id);
      onApply(result.access_point_device_id, position); setApplied(`Posición aplicada: (${position.x}, ${position.y}, ${position.z}) m. Puedes deshacerla; vuelve a calcular para evaluar el proyecto actual.`);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  function inputs(labels: string[], values: string[], update: (values: string[]) => void) {
    return labels.map((label, index) => <label className="field" key={label}><span>{label}</span><input type="number" step="any" aria-label={label} value={values[index]}
      onChange={event => update(values.map((value, i) => i === index ? event.target.value : value))} /></label>);
  }
  const name = (id: string | null) => project.devices.find(device => device.id === id)?.name ?? id ?? 'Sin datos';
  return <section className="panel results-panel analysis-panel" aria-labelledby="placement-title" aria-busy={analysis.pending}>
    <span className="eyebrow">ALTERNATIVAS REALIZABLES · UN AP</span><h2 id="placement-title">Compara lugares permitidos para el AP.</h2>
    <p className="helper">El motor compara márgenes en ambos sentidos de los enlaces prioritarios. La persona declara dónde hay alimentación, cableado y montaje posibles. Lugares y resultados de esta búsqueda son de sesión.</p>
    <fieldset className="inspector-fields" disabled={disabled}><legend className="sr-only">Parámetros de búsqueda de ubicación</legend>
      <label className="field"><span>Equipo y radio del AP a mover</span><select aria-label="Equipo y radio del AP a mover" value={apKey} onChange={event => edit(() => {
        setAP(event.target.value); setPriorities([]); setPoints([]); setZones([]); setConfirmed(false);
      })}><option value="">Seleccionar AP…</option>{options.map(option => <option key={option.key} value={option.key}>{option.device.name} · {option.radio.id}</option>)}</select></label>
      <fieldset className="priority-targets"><legend>Equipos prioritarios</legend>
        <p className="helper">Sin selección se evalúan todos los equipos enlazados con esa radio. Cada radio/enlace conserva sus datos.</p>
        <button type="button" onClick={() => edit(() => setPriorities([]))}>Evaluar todos los enlazados</button>
        {targetDevices.map(device => <label key={device.id}><input type="checkbox" checked={priorities.includes(device.id)} onChange={event => edit(() => setPriorities(previous => event.target.checked ? [...previous, device.id] : previous.filter(id => id !== device.id)))} /> {device.name}</label>)}
        {!targetDevices.length && <p className="helper">No hay equipos enlazados con esta radio. Crea los enlaces antes de buscar.</p>}
      </fieldset>
      <div className="allowed-place-forms"><form onSubmit={addPoint} noValidate><h3>Añadir un lugar exacto</h3>
        <label className="field"><span>Etiqueta del lugar</span><input aria-label="Etiqueta del lugar" value={pointLabel} maxLength={160} onChange={event => setPointLabel(event.target.value)} /></label>
        <div className="analysis-fields">{inputs(['Lugar X · m', 'Lugar Y · m', 'Altura del lugar · m'], pointFields, setPointFields)}</div><button type="submit">Añadir lugar permitido</button>
      </form><form onSubmit={addZone} noValidate><h3>Añadir una zona rectangular</h3>
        <label className="field"><span>Etiqueta de la zona</span><input aria-label="Etiqueta de la zona" value={zoneLabel} maxLength={160} onChange={event => setZoneLabel(event.target.value)} /></label>
        <div className="analysis-fields">{inputs(['Zona X mínimo · m', 'Zona Y mínimo · m', 'Zona X máximo · m', 'Zona Y máximo · m', 'Altura de la zona · m', 'Paso de la zona · m'], zoneFields, setZoneFields)}</div>
        <button type="submit">Añadir zona permitida</button><p className="helper">Paso 0,25–10 m. Se incluyen los puntos de la rejilla desde el mínimo, sin rebasar los máximos.</p>
      </form></div>
      <ul className="allowed-places">{points.map(point => <li key={point.id}>{point.label}: ({point.position.x}, {point.position.y}, {point.position.z}) m <button type="button" aria-label={`Retirar lugar ${point.label}`} onClick={() => edit(() => setPoints(previous => previous.filter(item => item.id !== point.id)))}>Retirar</button></li>)}
        {zones.map(zone => <li key={zone.id}>{zone.label}: X {zone.min_x_m}–{zone.max_x_m}, Y {zone.min_y_m}–{zone.max_y_m}, altura {zone.height_m} m · {zoneCount(zone)} posiciones <button type="button" aria-label={`Retirar zona ${zone.label}`} onClick={() => edit(() => setZones(previous => previous.filter(item => item.id !== zone.id)))}>Retirar</button></li>)}</ul>
      <p className="helper">{places} posiciones declaradas · máximo 2000. Los campos de un lugar o zona solo entran en la búsqueda después de añadirlos.</p>
      <label className="reference-toggle"><input type="checkbox" checked={confirmed} onChange={event => edit(() => setConfirmed(event.target.checked))} /> Confirmo alimentación, cableado y montaje viables en los lugares declarados.</label>
      <div className="analysis-actions"><button className="primary" type="button" disabled={analysis.pending || !places} onClick={run}>Buscar ubicaciones del AP</button>
        {analysis.pending && <button type="button" onClick={analysis.clear}>Descartar respuesta de búsqueda</button>}</div>
    </fieldset>
    {(error || analysis.error) && <p role="alert" className="message error">{error || analysis.error}</p>}
    <p role="status">{analysis.pending ? 'Evaluando lugares permitidos…' : applied || (result ? 'Búsqueda disponible para esta instalación.' : 'Sin búsqueda vigente.')}</p>
    {result && <><p className="helper">{result.evaluated} posiciones evaluadas · {result.excluded.length} excluidas · {result.elapsed_ms.toFixed(1)} ms · {result.ranked ? 'Orden por enlaces completos, peor margen y media.' : 'Sin orden: ningún lugar dispone de márgenes completos.'}</p>
      <p>Actual: peor margen {number(result.baseline.worst_margin_db)} dB · limitante {name(result.baseline.worst_target_id)} · {result.baseline.complete_targets} enlaces completos.</p>
      {!!result.ranking.length && <label className="field"><span>Alternativa de ubicación</span><select aria-label="Alternativa de ubicación" value={alternative?.candidate_id ?? ''} onChange={event => setSelected(event.target.value)}>
        {result.ranking.map(candidate => <option key={candidate.candidate_id} value={candidate.candidate_id}>{candidate.label} · ({candidate.position.x}, {candidate.position.y}, {candidate.position.z}) m · margen {number(candidate.worst_margin_db)} dB</option>)}</select></label>}
      {alternative && <><p>Alternativa: peor margen {number(alternative.worst_margin_db)} dB · limitante {name(alternative.worst_target_id)} · {alternative.complete_targets} enlaces completos.
        {' '}Cambio comparable: {number(comparablePlacementDelta(result.baseline, alternative), true)} dB.</p>
        <div className="table-scroll"><table><caption>Márgenes por enlace en dB · AP→equipo y equipo→AP</caption><thead><tr><th>Equipo y enlace</th><th>Actual ida / vuelta</th><th>Alternativa ida / vuelta</th><th>Limitante y datos de alternativa</th></tr></thead><tbody>
          {alternative.targets.map(target => { const baseline = result.baseline.targets.find(item => item.link_id === target.link_id); return <tr key={target.link_id}>
            <td>{name(target.device_id)}<small className="link-radio-pair">Radio del AP {result.access_point_radio_id} ↔ {(() => { const link = project.links.find(item => item.id === target.link_id); return link?.source_device_id === target.device_id ? link.source_radio_id : link?.target_radio_id; })()}</small></td><td>{number(baseline?.forward_margin_db ?? null)} / {number(baseline?.reverse_margin_db ?? null)}</td>
            <td>{number(target.forward_margin_db)} / {number(target.reverse_margin_db)}</td><td>{number(target.limiting_margin_db)} · {target.limiting_direction === 'forward' ? 'AP→equipo' : target.limiting_direction === 'reverse' ? 'equipo→AP' : 'Sin sentido limitante'}<br />{target.status === 'complete' ? 'Ambos sentidos calculados' : target.status === 'incomplete' ? 'Datos incompletos' : 'Sin calcular'}{target.reason && ` · ${targetReason(target.reason)}`}</td></tr>; })}
        </tbody></table></div><button type="button" disabled={disabled} onClick={apply}>Aplicar esta posición al AP</button></>}
      {!!result.excluded.length && <details><summary>Lugares excluidos ({result.excluded.length})</summary><ul>{result.excluded.map((item, index) => <li key={index}>({item.position.x}, {item.position.y}, {item.position.z}) m · {item.reason.startsWith('inside-wall:') ? `Dentro de la pared ${project.building.walls.findIndex(wall => wall.id === item.reason.slice('inside-wall:'.length)) + 1}` : item.reason}</li>)}</ul></details>}
      <details open className="limitations"><summary>Datos pendientes, alcance y límites</summary><p>{result.scope}</p><ul>{[...result.reasons, ...result.limitations].map((reason, index) => <li key={index}>{reason}</li>)}</ul></details>
    </>}
    <p className="comparison-limit">La búsqueda usa trayecto directo sin calibración experimental. Ordenar márgenes no clasifica cobertura ni aconseja compras. Los enlaces incompletos no influyen en el margen del orden; revisa cuáles faltan. Añadir AP y su conexión de datos queda fuera de esta búsqueda.</p>
  </section>;
}
