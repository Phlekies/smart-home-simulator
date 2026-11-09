import { useCallback, useEffect, useRef, useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import type { CoverageMapJob, CoverageMapResult } from './generated/coverage-map';
import type { ProjectFingerprint } from './generated/project-fingerprint';
import type { Project } from './generated/project';
import { api } from './api';
import { downloadText } from './editor/files';
import { mapColor, mapGridDimensions, metricNames, rasterCellSize } from './editor/coverage';
import type { CoverageLayer, CoverageRequest, MapMetric } from './editor/coverage';
import { CoverageRunner } from './editor/coverageRunner';
import type { MapState } from './editor/coverageRunner';
import { MAX_SAVED_MAP_BYTES, parseSavedMap, savedMapFileName, savedMapMismatch } from './editor/savedMap';
import { useAnalysis } from './useAnalysis';
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
function restoreFocusOnRemoval(button: HTMLButtonElement | null, fallback: HTMLButtonElement | null) {
  if (!button || !fallback) return;
  return () => {
    if (document.activeElement === button && fallback.isConnected && !fallback.disabled) fallback.focus();
  };
}
type OpenedMap = { name: string; map: CoverageMapResult };
async function checkOpenedMap(opened: OpenedMap, project: Project, signal: AbortSignal) {
  const fingerprint = await api<ProjectFingerprint>('/projects/fingerprint', project, signal);
  return { ...opened, mismatch: savedMapMismatch(opened.map, fingerprint, project) };
}

export default function CoveragePanel({ project, projectRevision, onLayer, onValidate, disabled }: {
  project: Project; projectRevision: number; onLayer: (layer: CoverageLayer | null) => void; onValidate: () => boolean;
  disabled: boolean;
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
  const calculateButton = useRef<HTMLButtonElement>(null);
  const openButton = useRef<HTMLButtonElement>(null);
  const cancelCalculateRef = useCallback((button: HTMLButtonElement | null) =>
    restoreFocusOnRemoval(button, calculateButton.current), []);
  const cancelOpenRef = useCallback((button: HTMLButtonElement | null) =>
    restoreFocusOnRemoval(button, openButton.current), []);
  const fileInput = useRef<HTMLInputElement>(null);
  const lastOpened = useRef<OpenedMap | null>(null);
  const latestProject = useRef(project);
  latestProject.current = project;
  const opening = useAnalysis<OpenedMap & { mismatch: string | null }>(projectRevision);
  const [runner] = useState(() => new CoverageRunner({ create: request => mapApi('', 'POST', request),
    read: id => mapApi(`/${id}`, 'GET'), cancel: id => mapApi(`/${id}`, 'DELETE') }, setJob));
  const options = project.devices.flatMap(device => device.radios.map(radio => ({ device, radio, key: key(device.id, radio.id) })));
  const ap = options.find(option => option.key === apKey), profile = options.find(option => option.key === profileKey);
  const active = ['submitting', 'queued', 'running'].includes(job.state);
  const opened = opening.result;
  const checking = opening.pending || (!!lastOpened.current && !opened && !opening.error);
  const calculated = calculatedRevision.current === projectRevision ? job.result : null;
  const result = disabled ? null : opened ? (opened.mismatch ? null : opened.map) : calculated;
  const resultAP = project.devices.find(device => device.id === result?.parameters.access_point_device_id);

  useEffect(() => {
    runner.invalidate();
    calculatedRevision.current = null;
    onLayer(null);
    const saved = lastOpened.current;
    // Never leave a previous revision on the plan. Wait until a drag pauses before checking its new fingerprint.
    const timer = saved ? window.setTimeout(() => {
      if (lastOpened.current === saved) opening.run(latestProject.current, (snapshot, signal) => checkOpenedMap(saved, snapshot, signal));
    }, 300) : undefined;
    return () => { window.clearTimeout(timer); runner.invalidate(true); };
  }, [projectRevision, runner, onLayer]);

  useEffect(() => {
    if (opened) lastOpened.current = opened;
  }, [opened]);

  function clearOpenedMap() {
    lastOpened.current = null;
    opening.clear();
  }

  function clearMap() {
    runner.invalidate();
    calculatedRevision.current = null;
    clearOpenedMap();
    onLayer(null);
    setError('');
  }
  function edit(action: () => void) { clearMap(); action(); }

  function openMap(event: ChangeEvent<HTMLInputElement>) {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = '';
    if (!file || disabled || !onValidate()) return;
    if (file.size > MAX_SAVED_MAP_BYTES) {
      setError('El mapa guardado supera el límite de 20 MB.');
      return;
    }
    clearMap();
    opening.run(project, async (snapshot, signal) => {
      const raw = await file.text();
      signal.throwIfAborted();
      return checkOpenedMap({ name: file.name, map: parseSavedMap(raw) }, snapshot, signal);
    });
  }

  useEffect(() => {
    if (!result) { onLayer(null); return; }
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
  }, [result, metric, onLayer]);

  function calculate(event: FormEvent) {
    event.preventDefault(); if (disabled || active || opening.pending || !onValidate()) return;
    try {
      const receiver = profileMode === 'generic' ? genericProfile : profile ? { id: profile.device.id, name: profile.device.name,
        radio: profile.radio, evidence: profile.device.evidence } : null;
      if (!ap || !receiver) throw new Error('Elige un emisor y un perfil válido con radio. Revisa los datos pendientes.');
      if (Object.entries(fields).some(([name, raw]) => (exact || !['px', 'py', 'pz'].includes(name)) && (raw.trim() === '' || !Number.isFinite(Number(raw))))) throw new Error('Completa los campos con números finitos.');
      const numbers = Object.fromEntries(Object.entries(fields).map(([name, raw]) => [name, Number(raw)])) as Record<keyof typeof fields, number>;
      const { x, y, width, depth, resolution, height, px, py, pz } = numbers;
      if (resolution < .1 || resolution > 5 || width <= 0 || depth <= 0 || width > 2000 || depth > 2000 || Math.abs(height) > 1000
        || x < -10000 || y < -10000 || x + width > 10000 || y + depth > 10000) throw new Error('Revisa área, altura y resolución: 0,1–5 m por celda, área dentro de ±10000 m y altura ±1000 m.');
      const dimensions = mapGridDimensions({ width_m: width, depth_m: depth, resolution_m: resolution });
      const cells = dimensions.columns * dimensions.rows;
      if (cells > 40000 || (cells + (exact ? 1 : 0)) * Math.max(1, project.building.walls.length) > 2000000) throw new Error('El mapa supera el límite de cálculo. Aumenta la resolución o reduce el área.');
      if (exact && (Math.abs(px) > 10000 || Math.abs(py) > 10000 || Math.abs(pz) > 1000)) throw new Error('El punto exacto está fuera de las coordenadas admitidas.');
      const request: CoverageRequest = { project, engine: 'quick-estimate', access_point_device_id: ap.device.id,
        access_point_radio_id: ap.radio.id, profile: receiver,
        grid: { origin_x_m: x, origin_y_m: y, width_m: width, depth_m: depth, resolution_m: resolution, height_m: height },
        points: exact ? [{ x: px, y: py, z: pz }] : [] };
      clearMap(); calculatedRevision.current = projectRevision; void runner.start(request);
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
  return <section className="results-panel panel coverage-panel" aria-labelledby="coverage-title">
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
      <div className="coverage-actions"><button ref={calculateButton} className="primary" disabled={!options.length} aria-disabled={active || opening.pending || undefined} type="submit">Calcular mapa</button>
        {active && <button ref={cancelCalculateRef} type="button" onClick={() => void runner.cancel()}>Cancelar mapa</button>}</div>
    </fieldset></form>
    <div className="coverage-actions" role="group" aria-label="Archivos de mapas de cobertura">
      <button type="button" ref={openButton} disabled={disabled} onClick={() => fileInput.current?.click()}>Abrir mapa JSON</button>
      <input type="file" accept=".json,application/json" hidden ref={fileInput} onChange={openMap} />
      <button type="button" disabled={!result} onClick={() => {
        if (result) downloadText(JSON.stringify(result, null, 2), savedMapFileName(result));
      }}>Guardar mapa JSON</button>
      {checking && <button ref={cancelOpenRef} type="button" onClick={clearOpenedMap}>Cancelar comprobación del mapa</button>}
    </div>
    <p className="helper">Los mapas JSON se guardan aparte del proyecto. Al abrirlos se comprueba la instalación y la versión del motor. Los parámetros del formulario se usan para el próximo cálculo.</p>
    {(error || job.error || opening.error) && <p className="message error" role="alert">{error || job.error || opening.error}</p>}
    <p role="status" className="comparison-state">{active ? `Mapa ${job.state === 'submitting' ? 'enviándose' : job.state === 'queued' ? 'en cola' : 'calculándose'} · ${Math.round(job.progress * 100)} %`
      : checking ? 'Comprobando el mapa guardado con la instalación actual…'
      : opened?.mismatch ? `Mapa guardado obsoleto: ${opened.name}. ${opened.mismatch} Calcula un mapa para la instalación actual.`
      : opened && result ? `Mapa guardado abierto: ${opened.name}. Mapa vigente en el plano 2D.`
      : job.state === 'cancelled' ? 'Mapa descartado; se ha solicitado cancelar el cálculo.'
      : result ? 'Mapa disponible en el plano 2D.' : 'Sin mapa vigente. Calcula de nuevo después de editar la instalación o los parámetros.'}</p>
    {active && <progress aria-label="Progreso del mapa" max={1} value={job.progress} />}
    <label className="field coverage-metric"><span>Métrica que se muestra en el plano</span><select aria-label="Métrica que se muestra en el plano" value={metric} onChange={event => setMetric(event.target.value as MapMetric)}>
      {(Object.keys(metricNames) as MapMetric[]).map(key => <option key={key} value={key}>{metricNames[key]} · {key.includes('margin') ? 'dB' : 'dBm'}</option>)}
    </select></label>
    <div className="coverage-legend"><span className="coverage-scale" /> <span>{metric.includes('margin') ? '≤ −30 a ≥ +40 dB' : '≤ −100 a ≥ −30 dBm'} · escala visual fija</span>
      <span>▧ Rayado: dato disponible con información parcial</span><span>■ Gris: sin valor de esta métrica</span><span>■ Gris oscuro: celda sin calcular</span></div>
    <p className="comparison-limit">Los colores no clasifican cobertura favorable o insuficiente. Estimador sin calibración experimental; no evalúa tráfico, interferencias ni estabilidad. Cambiar la instalación retira el mapa anterior.</p>
    {result && <>
      <div className="result-meta"><span>AP: {resultAP?.name ?? result.parameters.access_point_device_id} · {result.parameters.access_point_radio_id}</span><span>Perfil: {result.parameters.profile.name} · {result.parameters.profile.radio.id}</span>
        <span>{result.frequency_hz / 1e6} MHz · altura {result.parameters.grid.height_m} m · resolución {result.parameters.grid.resolution_m} m</span>
        <span>{result.columns}×{result.rows} celdas · {result.elapsed_ms.toFixed(1)} ms</span><span title={result.request_hash}>Mapa {result.request_hash.slice(0, 10)}</span></div>
      <p className="helper">{result.computed_cells} completas · {result.partial_cells} parciales · {result.not_computed_cells} sin calcular. Compatibilidad de radio: {result.compatibility === 'unverified' ? 'sin verificar' : 'compatible bajo los parámetros declarados'}.</p>
      {result.points.map((point, index) => {
        const { x, y, z } = result.parameters.points[index];
        return <div className="coverage-point" key={index}><h3>Punto exacto · X {x}, Y {y}, altura {z} m</h3>
          <p>AP → perfil: {value(point.forward_dbm, 'dBm')} · margen {value(point.forward_margin_db, 'dB')}.</p>
          <p>Perfil → AP: {value(point.reverse_dbm, 'dBm')} · margen {value(point.reverse_margin_db, 'dB')}.</p>
          <p>{point.status === 'not-computed' ? `Sin calcular: ${point.reason === 'inside-wall' ? 'dentro de una pared' : point.reason === 'too-close-to-access-point' ? 'demasiado próximo al AP' : point.reason ?? 'motivo no indicado'}.` : point.status === 'partial' ? 'Información parcial; faltan datos para uno o más valores.' : 'Presupuesto calculado en ambos sentidos; no garantiza una conexión fiable.'}</p></div>;
      })}
      <details className="limitations"><summary>Supuestos, datos pendientes y límites del mapa</summary><p>{result.scope}</p><p>Perfil: {result.parameters.profile.evidence}</p>
        <ul>{[...result.reasons, ...result.limitations].map((text, index) => <li key={index}>{text}</li>)}</ul></details>
    </>}
  </section>;
}
