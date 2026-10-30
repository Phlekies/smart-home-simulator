import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import type { CoverageMapJob } from './generated/coverage-map';
import type { Project } from './generated/project';
import { mapColor, metricNames, rasterCellSize } from './editor/coverage';
import type { CoverageLayer, CoverageRequest, MapMetric } from './editor/coverage';
import { CoverageRunner } from './editor/coverageRunner';
import type { MapState } from './editor/coverageRunner';
import GenericProfilePicker from './GenericProfilePicker';
import type { ReceiverProfile } from './generated/coverage-map';

async function mapApi(path: string, method: string, body?: unknown): Promise<CoverageMapJob> {
  const response = await fetch(`/api/coverage-maps${path}`, { method,
    ...(body ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}) });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `La API rechazó el mapa (${response.status}). Revisa los parámetros y las radios.`);
  return data as CoverageMapJob;
}
const key = (device: string, radio: string) => JSON.stringify([device, radio]);
const value = (n: number | null, unit: string) => n === null ? 'Sin datos' : `${n.toFixed(1)} ${unit}`;

export default function CoveragePanel({ project, projectRevision, onLayer, onValidate, disabled }: {
  project: Project; projectRevision: number; onLayer: (layer: CoverageLayer | null) => void; onValidate: () => boolean; disabled: boolean;
}) {
  const firstAP = project.devices.find(device => ['access-point', 'controller'].includes(device.role)) ?? project.devices[0];
  const firstProfile = project.devices.find(device => device.id !== firstAP?.id) ?? firstAP;
  const [apKey, setAP] = useState(firstAP ? key(firstAP.id, firstAP.radios[0].id) : '');
  const [profileKey, setProfile] = useState(firstProfile ? key(firstProfile.id, firstProfile.radios[0].id) : '');
  const [profileMode, setProfileMode] = useState<'device' | 'generic'>('device');
  const [genericProfile, setGenericProfile] = useState<ReceiverProfile | null>(null);
  const [fields, setFields] = useState({ x: '0', y: '0', width: String(project.building.width_m), depth: String(project.building.depth_m),
    resolution: '0.5', height: String(firstProfile?.position.z ?? 1.4), px: String(firstProfile?.position.x ?? 0),
    py: String(firstProfile?.position.y ?? 0), pz: String(firstProfile?.position.z ?? 1.4) });
  const [exact, setExact] = useState(false);
  const [metric, setMetric] = useState<MapMetric>('forward_dbm');
  const [error, setError] = useState('');
  const [job, setJob] = useState<MapState>({ state: 'idle', progress: 0, result: null, error: null });
  const calculatedRevision = useRef<number | null>(null);
  const [runner] = useState(() => new CoverageRunner({ create: request => mapApi('', 'POST', request),
    read: id => mapApi(`/${id}`, 'GET'), cancel: id => mapApi(`/${id}`, 'DELETE') }, setJob));
  const options = project.devices.flatMap(device => device.radios.map(radio => ({ device, radio, key: key(device.id, radio.id) })));
  const ap = options.find(option => option.key === apKey), profile = options.find(option => option.key === profileKey);
  const active = ['submitting', 'queued', 'running'].includes(job.state);

  useEffect(() => { runner.invalidate(); calculatedRevision.current = null; onLayer(null);
    return () => runner.invalidate(true); }, [projectRevision, runner, onLayer]);
  function edit(action: () => void) { runner.invalidate(); calculatedRevision.current = null; onLayer(null); setError(''); action(); }

  useEffect(() => {
    const result = job.result;
    if (!result || calculatedRevision.current !== projectRevision) { onLayer(null); return; }
    const size = rasterCellSize(result.columns, result.rows), canvas = document.createElement('canvas');
    canvas.width = result.columns * size; canvas.height = result.rows * size;
    const ctx = canvas.getContext('2d'); if (!ctx) { setError('El navegador no pudo dibujar el mapa.'); onLayer(null); return; }
    const values = result.cells[metric];
    values.forEach((number, index) => {
      const x = index % result.columns * size, y = Math.floor(index / result.columns) * size;
      ctx.fillStyle = result.cells.status[index] === 'not-computed' ? '#3d474d' : mapColor(number, metric);
      ctx.fillRect(x, y, size, size);
      if (result.cells.status[index] === 'partial' && number !== null) {
        ctx.strokeStyle = '#ffffff66'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x, y + size); ctx.lineTo(x + size, y); ctx.stroke();
      }
    });
    const imageUrl = canvas.toDataURL('image/png');
    if (imageUrl === 'data:,') { setError('El navegador no pudo dibujar estas dimensiones. Reduce el área o aumenta la resolución.'); onLayer(null); return; }
    onLayer({ result, metric, imageUrl });
  }, [job.result, metric, projectRevision, onLayer]);

  function calculate(event: FormEvent) {
    event.preventDefault(); if (disabled || !onValidate()) return;
    try {
      const receiver = profileMode === 'generic' ? genericProfile : profile ? { id: profile.device.id, name: profile.device.name,
        radio: profile.radio, evidence: profile.device.evidence } : null;
      if (!ap || !receiver) throw new Error('Elige un emisor y un perfil válido con radio. Revisa los datos pendientes.');
      if (Object.entries(fields).some(([name, raw]) => (exact || !['px', 'py', 'pz'].includes(name)) && (raw.trim() === '' || !Number.isFinite(Number(raw))))) throw new Error('Completa los campos con números finitos.');
      const numbers = Object.fromEntries(Object.entries(fields).map(([name, raw]) => [name, Number(raw)])) as Record<keyof typeof fields, number>;
      const { x, y, width, depth, resolution, height, px, py, pz } = numbers;
      if (resolution < .1 || resolution > 5 || width <= 0 || depth <= 0 || width > 2000 || depth > 2000 || Math.abs(height) > 1000
        || x < -10000 || y < -10000 || x + width > 10000 || y + depth > 10000) throw new Error('Revisa área, altura y resolución: 0,1–5 m por celda, área dentro de ±10000 m y altura ±1000 m.');
      const cells = Math.ceil(width / resolution - 1e-9) * Math.ceil(depth / resolution - 1e-9);
      if (cells > 40000 || (cells + (exact ? 1 : 0)) * Math.max(1, project.building.walls.length) > 2000000) throw new Error('El mapa supera el límite de cálculo. Aumenta la resolución o reduce el área.');
      if (exact && (Math.abs(px) > 10000 || Math.abs(py) > 10000 || Math.abs(pz) > 1000)) throw new Error('El punto exacto está fuera de las coordenadas admitidas.');
      const request: CoverageRequest = { project, engine: 'quick-estimate', access_point_device_id: ap.device.id,
        access_point_radio_id: ap.radio.id, profile: receiver,
        grid: { origin_x_m: x, origin_y_m: y, width_m: width, depth_m: depth, resolution_m: resolution, height_m: height },
        points: exact ? [{ x: px, y: py, z: pz }] : [] };
      setError(''); calculatedRevision.current = projectRevision; void runner.start(request);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  function number(name: keyof typeof fields, label: string, min: number, max: number) {
    return <label className="field"><span>{label}</span><input type="number" value={fields[name]} min={min} max={max} step="any" required
      onChange={event => edit(() => setFields(previous => ({ ...previous, [name]: event.target.value })))} /></label>;
  }
  function choose(value: string, update: (value: string) => void, label: string) {
    return <label className="field"><span>{label}</span><select aria-label={label} value={value} onChange={event => edit(() => update(event.target.value))}>
      <option value="">Seleccionar equipo y radio…</option>{options.map(option => <option key={option.key} value={option.key}>
        {option.device.name} · {option.radio.id} · {option.radio.frequency_hz / 1e6} MHz</option>)}
    </select></label>;
  }
  const result = job.result && calculatedRevision.current === projectRevision ? job.result : null;
  const point = result?.points[0];
  return <section className="results-panel panel coverage-panel" aria-labelledby="coverage-title" aria-busy={disabled || active}>
    <span className="eyebrow">SEÑAL EN EL PLANO · TRAYECTO DIRECTO</span><h2 id="coverage-title">Mapa para un equipo y una altura.</h2>
    <p className="helper">Elige qué equipo representa el AP y qué radio representa el cliente. Sus parámetros actuales se usan sin completar datos desconocidos. Un único AP por mapa.</p>
    <form onSubmit={calculate} noValidate><fieldset className="inspector-fields" disabled={disabled}><legend className="sr-only">Parámetros del mapa</legend>
      <label className="field"><span>Origen del perfil receptor</span><select aria-label="Origen del perfil receptor" value={profileMode} onChange={event => edit(() => setProfileMode(event.target.value as typeof profileMode))}>
        <option value="device">Radio de un equipo del proyecto</option><option value="generic">Perfil Wi-Fi genérico con procedencia</option></select></label>
      <div className="coverage-fields">{choose(apKey, setAP, 'Emisor / AP del mapa')}{profileMode === 'device' && choose(profileKey, setProfile, 'Equipo y radio del perfil receptor')}
        {number('height', 'Altura del mapa · m', -1000, 1000)}{number('resolution', 'Resolución del mapa · m', .1, 5)}
        {number('x', 'Origen X del mapa · m', -10000, 10000)}{number('y', 'Origen Y del mapa · m', -10000, 10000)}
        {number('width', 'Ancho del mapa · m', .000001, 2000)}{number('depth', 'Fondo del mapa · m', .000001, 2000)}
      </div>
      {profileMode === 'generic' && <GenericProfilePicker apRadio={ap?.radio} onChange={next => edit(() => setGenericProfile(next))} />}
      <label className="reference-toggle"><input type="checkbox" checked={exact} onChange={event => edit(() => setExact(event.target.checked))} /> Evaluar también un punto exacto</label>
      {exact && <div className="coverage-fields">{number('px', 'Punto exacto X · m', -10000, 10000)}{number('py', 'Punto exacto Y · m', -10000, 10000)}{number('pz', 'Altura del punto exacto · m', -1000, 1000)}</div>}
      <div className="coverage-actions"><button className="primary" disabled={active || !options.length} type="submit">Calcular mapa</button>
        {active && <button type="button" onClick={() => void runner.cancel()}>Cancelar mapa</button>}</div>
    </fieldset></form>
    {(error || job.error) && <p className="message error" role="alert">{error || job.error}</p>}
    <p role="status" className="comparison-state">{active ? `Mapa ${job.state === 'submitting' ? 'enviándose' : job.state === 'queued' ? 'en cola' : 'calculándose'} · ${Math.round(job.progress * 100)} %`
      : job.state === 'cancelled' ? 'Mapa descartado; se ha solicitado cancelar el cálculo.' : result ? 'Mapa disponible en el plano 2D.' : 'Sin mapa vigente. Calcula de nuevo después de editar la instalación o los parámetros.'}</p>
    {active && <progress aria-label="Progreso del mapa" max={1} value={job.progress} />}
    <label className="field coverage-metric"><span>Métrica que se muestra en el plano</span><select aria-label="Métrica que se muestra en el plano" value={metric} onChange={event => setMetric(event.target.value as MapMetric)}>
      {(Object.keys(metricNames) as MapMetric[]).map(key => <option key={key} value={key}>{metricNames[key]} · {key.includes('margin') ? 'dB' : 'dBm'}</option>)}
    </select></label>
    <div className="coverage-legend"><span className="coverage-scale" /> <span>{metric.includes('margin') ? '≤ −30 a ≥ +40 dB' : '≤ −100 a ≥ −30 dBm'} · escala visual fija</span>
      <span>▧ Rayado: dato disponible con información parcial</span><span>■ Gris: sin valor de esta métrica</span><span>■ Gris oscuro: celda sin calcular</span></div>
    <p className="comparison-limit">Los colores no clasifican cobertura favorable o insuficiente. Estimador sin calibración experimental; no evalúa tráfico, interferencias ni estabilidad. Cambiar la instalación retira el mapa anterior.</p>
    {result && <>
      <div className="result-meta"><span>AP: {ap?.device.name} · {result.parameters.access_point_radio_id}</span><span>Perfil: {result.parameters.profile.name} · {result.parameters.profile.radio.id}</span>
        <span>{result.frequency_hz / 1e6} MHz · altura {result.parameters.grid.height_m} m · resolución {result.parameters.grid.resolution_m} m</span>
        <span>{result.columns}×{result.rows} celdas · {result.elapsed_ms.toFixed(1)} ms</span><span title={result.request_hash}>Mapa {result.request_hash.slice(0, 10)}</span></div>
      <p className="helper">{result.computed_cells} completas · {result.partial_cells} parciales · {result.not_computed_cells} sin calcular. Compatibilidad de radio: {result.compatibility === 'unverified' ? 'sin verificar' : 'compatible bajo los parámetros declarados'}.</p>
      {exact && point && <div className="coverage-point"><h3>Punto exacto · X {result.parameters.points[0].x}, Y {result.parameters.points[0].y}, altura {result.parameters.points[0].z} m</h3>
        <p>AP → perfil: {value(point.forward_dbm, 'dBm')} · margen {value(point.forward_margin_db, 'dB')}.</p>
        <p>Perfil → AP: {value(point.reverse_dbm, 'dBm')} · margen {value(point.reverse_margin_db, 'dB')}.</p>
        <p>{point.status === 'not-computed' ? `Sin calcular: ${point.reason === 'inside-wall' ? 'dentro de una pared' : point.reason === 'too-close-to-access-point' ? 'demasiado próximo al AP' : point.reason ?? 'motivo no indicado'}.` : point.status === 'partial' ? 'Información parcial; faltan datos para uno o más valores.' : 'Presupuesto calculado en ambos sentidos; no garantiza una conexión fiable.'}</p></div>}
      <details className="limitations"><summary>Supuestos, datos pendientes y límites del mapa</summary><p>{result.scope}</p><p>Perfil: {result.parameters.profile.evidence}</p>
        <ul>{[...result.reasons, ...result.limitations].map((text, index) => <li key={index}>{text}</li>)}</ul></details>
    </>}
  </section>;
}
