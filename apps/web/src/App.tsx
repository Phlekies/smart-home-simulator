import { Component, Suspense, lazy, useEffect, useRef, useState } from 'react';
import type { ChangeEvent, ReactNode } from 'react';
import { api } from './api';
import Plan from './Plan';
import WallInspector from './WallInspector';
import { adoptHistory, editHistory, emptyHistory, finishGesture, redoHistory, startGesture, undoHistory } from './editor/history';
import { translateWall } from './editor/geometry';
import type { Device, Point, Project, Radio } from './generated/project';
import type { SimulationResult } from './generated/simulation-result';

const Scene3D = lazy(() => import('./Scene3D'));
type Engine = { id: string; name: string; available: boolean; description: string };
const statusNames = { 'above-threshold': 'Sobre umbral', 'below-threshold': 'Bajo umbral',
  incompatible: 'Incompatible', unverified: 'Sin verificar', unsupported: 'Fuera de alcance' };

class SceneBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? <p className="scene-error">No se pudo iniciar la vista 3D. Puedes seguir trabajando en Plano 2D.</p> : this.props.children; }
}

function NumberField({ label, value, onChange, min, max, step = .1, nullable = false }: {
  label: string; value: number | null; onChange: (n: number | null) => void;
  min?: number; max?: number; step?: number; nullable?: boolean;
}) {
  return <label className="field"><span>{label}</span><input type="number" value={value ?? ''} min={min} max={max}
    step={step} placeholder={nullable ? 'Desconocido' : undefined} onChange={event => {
      if (event.target.value === '') { if (nullable) onChange(null); return; }
      const n = Number(event.target.value);
      if (Number.isFinite(n) && (min === undefined || n >= min) && (max === undefined || n <= max)) onChange(n);
    }} /></label>;
}

function newProject(materials?: Project['building']['materials']): Project {
  return { format: 'smart-environment-simulator', version: 1, name: 'Mi entorno inteligente', units: 'm',
    building: { width_m: 12, depth_m: 10, materials: materials ? structuredClone(materials) : [{ id: 'drywall', name: 'Tabique genérico',
      loss_db_24ghz: 3, loss_db_5ghz: 5, extra_loss_db_per_cm: 0, evidence: 'Hipótesis empírica sin calibrar' }],
    walls: [[0, 0, 12, 0], [12, 0, 12, 10], [12, 10, 0, 10], [0, 10, 0, 0]].map(([x, y, x2, y2], index) => ({
      id: `wall-${index}`, start: { x, y, z: 0 }, end: { x: x2, y: y2, z: 0 }, height_m: 2.6,
      thickness_m: .12, material_id: materials?.[0].id ?? 'drywall',
    })) }, devices: [], links: [], settings: { path_loss_exponent: 2.1, extra_loss_db_per_m: 0, system_gain_db: 0 },
    migration_notes: [], legacy_source: null };
}

export default function App() {
  const [history, setHistory] = useState(() => emptyHistory<Project>());
  const historyRef = useRef(history);
  historyRef.current = history;
  const project = history.present;
  const gestureChanged = history.gestureBase !== null && JSON.stringify(history.present) !== JSON.stringify(history.gestureBase);
  const canUndo = history.past.length > 0 || gestureChanged;
  const canRedo = history.future.length > 0 && !gestureChanged;
  const [selected, setSelected] = useState('');
  const [selectedWallId, setSelectedWallId] = useState<string | null>(null);
  const [tool, setTool] = useState<'select' | 'wall'>('select');
  const [radioId, setRadioId] = useState('');
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [engines, setEngines] = useState<Engine[]>([]);
  const [view, setView] = useState<'2d' | '3d'>('2d');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [exampleId, setExampleId] = useState('apartment');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const revision = useRef(0);
  const loadSequence = useRef(0);
  const fileInput = useRef<HTMLInputElement>(null);

  function adopt(next: Project) {
    revision.current += 1;
    setHistory(previous => adoptHistory(previous, next));
    setSelected(next.devices[0]?.id ?? ''); setSelectedWallId(null); setTool('select'); setRadioId(''); setResult(null); setError(''); setExampleId('');
  }
  async function loadExample(id: string) {
    const sequence = ++loadSequence.current;
    setLoading(true); setError(''); setNotice('');
    try {
      const next = await api<Project>(`/examples/${id}`);
      if (sequence === loadSequence.current) { adopt(next); setExampleId(id); }
    } catch (e) { if (sequence === loadSequence.current) setError(`No se pudo abrir el ejemplo. ${String(e)}`); }
    finally { if (sequence === loadSequence.current) setLoading(false); }
  }
  useEffect(() => {
    void loadExample('apartment');
    void api<Engine[]>('/engines').then(setEngines).catch(() => setEngines([]));
    return () => { loadSequence.current += 1; };
  }, []);

  function change(edit: (p: Project) => void) {
    revision.current += 1; setResult(null); setNotice('Cambios pendientes de simular.');
    setHistory(previous => editHistory(previous, edit));
  }
  function selectDevice(id: string) { setSelected(id); setSelectedWallId(null); }
  function selectWall(id: string) { setSelected(''); setSelectedWallId(id); }
  function beginGesture() { setHistory(startGesture); }
  function endGesture() { setHistory(finishGesture); }
  function travelHistory(direction: 'undo' | 'redo') {
    const current = historyRef.current;
    const changed = current.gestureBase !== null && JSON.stringify(current.present) !== JSON.stringify(current.gestureBase);
    if (direction === 'undo' ? !current.past.length && !changed : !current.future.length || changed) return;
    revision.current += 1; setResult(null); setTool('select');
    setHistory(previous => direction === 'undo' ? undoHistory(previous) : redoHistory(previous));
    setNotice(direction === 'undo' ? 'Cambio deshecho. Ejecuta una nueva estimación.' : 'Cambio rehecho. Ejecuta una nueva estimación.');
  }
  useEffect(() => {
    function keyboard(event: KeyboardEvent) {
      const target = event.target;
      if (target instanceof HTMLElement && (target.isContentEditable || target.closest('input, textarea, select'))) return;
      if ((event.ctrlKey || event.metaKey) && !event.altKey && (event.key.toLowerCase() === 'z' || event.key.toLowerCase() === 'y')) {
        event.preventDefault(); travelHistory(event.shiftKey || event.key.toLowerCase() === 'y' ? 'redo' : 'undo');
      }
    }
    document.addEventListener('keydown', keyboard);
    return () => document.removeEventListener('keydown', keyboard);
  }, []);
  const device = project?.devices.find(d => d.id === selected);
  const wall = project?.building.walls.find(w => w.id === selectedWallId);
  const radio = device?.radios.find(r => r.id === radioId) ?? device?.radios[0];
  function editDevice(patch: Partial<Device>) {
    change(p => { const d = p.devices.find(d => d.id === selected); if (d) Object.assign(d, patch); });
  }
  function editRadio(patch: Partial<Radio>) {
    change(p => { const d = p.devices.find(d => d.id === selected); const r = d?.radios.find(r => r.id === radio?.id); if (r) Object.assign(r, patch); });
  }
  async function run() {
    if (!project) return;
    const current = revision.current;
    setBusy(true); setError(''); setNotice('');
    try {
      const computed = await api<SimulationResult>('/simulations', { project, engine: 'quick-estimate' });
      if (current === revision.current) { setResult(computed); setNotice('Estimación completada. Revisa los límites y datos pendientes.'); }
      else setNotice('El proyecto cambió durante el cálculo. Ejecuta una nueva estimación.');
    } catch (e) { if (current === revision.current) setError(`No se pudo simular. ${String(e)}`); }
    finally { setBusy(false); }
  }
  async function importFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]; event.target.value = '';
    if (!file) return;
    if (file.size > 2_000_000) { setError('El archivo supera el límite local de 2 MB.'); return; }
    const sequence = ++loadSequence.current;
    setLoading(true);
    try {
      const next = await api<Project>('/projects/import', JSON.parse(await file.text()));
      if (sequence === loadSequence.current) { adopt(next); setNotice(`Abierto: ${file.name}`); }
    } catch (e) { if (sequence === loadSequence.current) setError(`Archivo no válido. ${String(e)}`); }
    finally { if (sequence === loadSequence.current) setLoading(false); }
  }
  function download(data: unknown, filename: string) {
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function saveProject() {
    if (!project) return;
    const current = revision.current;
    try {
      const validated = await api<Project>('/projects/import', project);
      if (current !== revision.current) { setNotice('El proyecto cambió durante la validación. Guarda de nuevo.'); return; }
      download(validated, 'entorno.shsim.json'); setNotice('Proyecto validado y guardado como JSON.');
    } catch (e) { setError(`Revisa los datos antes de guardar. ${String(e)}`); }
  }
  function addDevice() {
    const id = crypto.randomUUID();
    change(p => p.devices.push({ id, name: `Dispositivo ${p.devices.length + 1}`, role: 'endpoint',
      position: { x: p.building.width_m / 2, y: p.building.depth_m / 2, z: 1.4 },
      evidence: 'Equipo genérico definido por el usuario; funciones sin verificar',
      radios: [{ id: 'radio-1', protocol: 'unknown', frequency_hz: 2.412e9, bandwidth_hz: 20e6, channel: null,
        tx_power_dbm: 0, tx_gain_dbi: 0, rx_gain_dbi: 0, sensitivity_dbm: null, noise_figure_db: 7,
        antenna: 'omnidirectional', orientation_deg: 0, beamwidth_deg: 360, pattern_sharpness: 1.8,
        side_lobe_attenuation_db: 18, polarization_deg: 0 }] }));
    selectDevice(id); setRadioId(''); setTool('select');
  }
  function addWall(start: Point, end: Point) {
    if (!project || project.building.walls.length >= 2000) return;
    const id = crypto.randomUUID();
    change(p => p.building.walls.push({ id, start, end, height_m: 2.6, thickness_m: .12, material_id: p.building.materials[0].id }));
    selectWall(id); setTool('select');
  }

  return <div className="application">
    <header className="app-header">
      <a className="brand" href="#workspace"><span className="brand-mark">S<span>∿</span></span>
        <span>smart environment<small>Diseña. Comprueba. Decide.</small></span></a>
      <div className="local-indicator"><i /> Proyecto local <span>·</span> Datos en tu equipo</div>
      <button className="primary" disabled={!project || busy || loading || !project.links.length} onClick={() => void run()}>
        {busy ? 'Calculando…' : '▷ Ejecutar estimación'}</button>
    </header>

    <main id="workspace">
      <section className="project-heading">
        <div><p className="eyebrow">PLANIFICADOR DE ENTORNOS INTELIGENTES</p><h1>Tu espacio, conectado.</h1>
          <p>Explora los enlaces de tu instalación y descubre qué falta comprobar.</p></div>
        <div className="file-actions">
          <button disabled={loading} onClick={() => { loadSequence.current += 1; adopt(newProject(project?.building.materials)); setNotice('Proyecto nuevo. Dibuja las paredes y añade dispositivos.'); }}>Nuevo</button>
          <button onClick={() => fileInput.current?.click()}>↥ Abrir proyecto</button>
          <button disabled={!project || loading} onClick={() => void saveProject()}>↧ Guardar JSON</button>
          <input ref={fileInput} type="file" accept=".json,application/json" hidden onChange={event => void importFile(event)} />
        </div>
      </section>

      {error && <div className="message error" role="alert">{error}</div>}
      <div className="message notice" role="status" aria-live="polite">{notice || (loading ? 'Abriendo proyecto…' : 'Arrastra los dispositivos en el plano o ajusta sus propiedades.')}</div>

      <section className="workspace-grid" aria-busy={loading}>
        <aside className="devices-panel panel">
          <div className="panel-heading"><span className="eyebrow">INSTALACIÓN</span><span className="count">{project?.devices.length ?? 0}</span></div>
          <h2>Dispositivos</h2>
          <label className="field example-field"><span>Explorar un ejemplo</span><select value={exampleId} disabled={loading} onChange={e => { if (e.target.value) void loadExample(e.target.value); }}>
            <option value="">Proyecto actual</option>
            <option value="apartment">Apartamento inteligente</option><option value="office">Oficina</option><option value="warehouse">Almacén</option>
          </select></label>
          <div className="device-list">{project?.devices.map(d => <button key={d.id} className={`device-item ${selected === d.id ? 'selected' : ''}`}
            onClick={() => { selectDevice(d.id); setRadioId(''); }}>
            <span className={`device-icon ${d.role === 'controller' || d.role === 'access-point' ? 'hub' : ''}`}>{d.role === 'controller' || d.role === 'access-point' ? '◈' : '◉'}</span>
            <span><strong>{d.name}</strong><small>{d.radios[0].protocol === 'unknown' ? 'Protocolo por verificar' : d.radios[0].protocol.toUpperCase()}</small></span>
          </button>)}</div>
          <button className="add-button" disabled={!project || loading || project.devices.length >= 128} onClick={addDevice}>＋ Añadir dispositivo</button>
          <details className="wall-list"><summary>Paredes · {project?.building.walls.length ?? 0}</summary>
            {project?.building.walls.map((w, index) => <button key={w.id} className={selectedWallId === w.id ? 'selected' : ''} onClick={() => selectWall(w.id)}>
              Pared {index + 1} · {project.building.materials.find(m => m.id === w.material_id)?.name}
            </button>)}
          </details>
          <div className="engine-card"><span className="eyebrow">CÁLCULO DISPONIBLE</span><strong>Estimación de enlaces</strong>
            <p>Trayecto directo y obstáculos. Sin calibración experimental.</p>
            {engines.filter(e => !e.available).map(e => <div className="engine-pending" key={e.id} title={e.description}>{e.name}<span>Pendiente</span></div>)}
          </div>
        </aside>

        <section className="scene-panel panel" aria-label="Editor del entorno">
          <div className="scene-toolbar"><div><span className="eyebrow">ESPACIO DE TRABAJO</span>
            <input className="project-name" aria-label="Nombre del proyecto" value={project?.name ?? ''} disabled={!project || loading}
              onChange={e => change(p => { p.name = e.target.value; })} /></div>
            <div className="segmented"><button aria-pressed={view === '2d'} onClick={() => setView('2d')}>Plano 2D</button>
              <button aria-pressed={view === '3d'} onClick={() => setView('3d')}>Vista 3D</button></div>
          </div>
          <div className="editor-toolbar" role="toolbar" aria-label="Herramientas del plano">
            <button disabled={!project || loading} aria-pressed={tool === 'select'} onClick={() => setTool('select')}>Seleccionar</button>
            <button disabled={!project || loading || project.building.walls.length >= 2000} aria-pressed={tool === 'wall'} onClick={() => { setView('2d'); setTool('wall'); }}>Dibujar pared</button>
            <span className="toolbar-divider" />
            <button disabled={!canUndo} onClick={() => travelHistory('undo')} title="Ctrl/Cmd+Z">↶ Deshacer</button>
            <button disabled={!canRedo} onClick={() => travelHistory('redo')} title="Ctrl/Cmd+Shift+Z">↷ Rehacer</button>
          </div>
          <p className="editor-hint" role="status">{tool === 'wall' ? 'Haz clic en el inicio y el final de la pared. Escape cancela. Ajuste a 0.1 m.' : 'Selecciona o arrastra paredes y equipos. Flechas mueven en el plano; Shift amplía el paso.'}</p>
          <div className="scene-content">{project ? view === '2d'
            ? <Plan project={project} selected={selected} onSelect={selectDevice} result={result}
              tool={tool} selectedWallId={selectedWallId} onSelectWall={selectWall} onAddWall={addWall}
              onGestureStart={beginGesture} onGestureEnd={endGesture}
              onMoveWall={(id, dx, dy) => change(p => {
                const index = p.building.walls.findIndex(w => w.id === id);
                if (index >= 0) {
                  try { p.building.walls[index] = translateWall(p.building.walls[index], dx, dy); } catch { /* Outside supported coordinates. */ }
                }
              })} onMove={(id, x, y) => change(p => {
              const d = p.devices.find(d => d.id === id); if (d) { d.position.x = x; d.position.y = y; }
            })} />
            : <SceneBoundary><Suspense fallback={<p className="scene-error">Preparando vista 3D…</p>}><Scene3D project={project} selected={selected} onSelect={selectDevice} selectedWallId={selectedWallId} onSelectWall={selectWall} /></Suspense></SceneBoundary>
            : <div className="scene-error"><h2>{loading ? 'Abriendo el espacio…' : 'Elige tu punto de partida'}</h2><p>Abre un ejemplo, importa un proyecto Java o crea una instalación nueva.</p>
              <button onClick={() => { loadSequence.current += 1; setLoading(false); adopt(newProject()); }}>Crear proyecto local</button></div>}</div>
          <div className="scene-footer"><span>◉ Dispositivo <span className="hub-dot">◆</span> Controlador / AP</span>
            <span>{view === '2d' ? 'Cuadrícula · 1 m · Una planta, sin forjados' : 'Arrastra para orbitar · Rueda para acercar'}</span></div>
        </section>

        <aside className="properties-panel panel">{wall && project ? <WallInspector key={wall.id} project={project} wall={wall}
          onGestureStart={beginGesture} onGestureEnd={endGesture}
          onEdit={next => change(p => { const index = p.building.walls.findIndex(w => w.id === next.id); if (index >= 0) p.building.walls[index] = next; })}
          onMaterialEdit={(id, patch) => change(p => { const material = p.building.materials.find(m => m.id === id); if (material) Object.assign(material, patch, { evidence: 'Valor editado por el usuario; sin calibración experimental' }); })}
          onDelete={() => { change(p => { p.building.walls = p.building.walls.filter(w => w.id !== wall.id); }); setSelectedWallId(null); }} />
          : <><span className="eyebrow">PROPIEDADES</span><h2>{device ? 'Ajusta el dispositivo' : 'Selecciona un objeto'}</h2>
          {device && radio ? <>
            <label className="field"><span>Nombre</span><input value={device.name} maxLength={160} onChange={e => editDevice({ name: e.target.value })} /></label>
            <label className="field"><span>Función en la instalación</span><select value={device.role} onChange={e => editDevice({ role: e.target.value as Device['role'] })}>
              <option value="endpoint">Dispositivo final</option><option value="controller">Controlador</option><option value="access-point">Punto de acceso</option>
              <option value="router">Router de malla</option><option value="bridge">Puente</option><option value="unknown">Sin verificar</option></select></label>
            <h3>Ubicación <small>metros</small></h3><div className="coordinate-fields">{(['x', 'y', 'z'] as const).map(axis => <NumberField key={axis} label={axis === 'z' ? 'Altura' : axis.toUpperCase()}
              value={device.position[axis]} step={.05} onChange={n => n !== null && editDevice({ position: { ...device.position, [axis]: n } })} />)}</div>
            <h3>Radio <small>datos configurados</small></h3>
            {device.radios.length > 1 && <label className="field"><span>Interfaz</span><select value={radio.id} onChange={e => setRadioId(e.target.value)}>
              {device.radios.map(r => <option key={r.id} value={r.id}>{r.id}</option>)}</select></label>}
            <label className="field"><span>Protocolo</span><select value={radio.protocol} onChange={e => editRadio({ protocol: e.target.value as Radio['protocol'] })}>
              <option value="unknown">Sin verificar</option>{['wifi', 'thread', 'zigbee', 'ble', 'zwave'].map(p => <option key={p} value={p}>{p.toUpperCase()}</option>)}
            </select></label>
            <div className="radio-fields"><NumberField label="Frecuencia · GHz" value={radio.frequency_hz / 1e9} min={.001} max={100} step={.001} onChange={n => n !== null && editRadio({ frequency_hz: n * 1e9 })} />
              <NumberField label="Canal" value={radio.channel} nullable min={0} max={1000} step={1} onChange={n => editRadio({ channel: n })} />
              <NumberField label="Potencia TX · dBm" value={radio.tx_power_dbm} nullable min={-100} max={100} onChange={n => editRadio({ tx_power_dbm: n })} />
              <NumberField label="Sensibilidad · dBm" value={radio.sensitivity_dbm} nullable min={-200} max={0} onChange={n => editRadio({ sensitivity_dbm: n })} />
              <NumberField label="Ancho · MHz" value={radio.bandwidth_hz / 1e6} min={.001} max={1000} onChange={n => n !== null && editRadio({ bandwidth_hz: n * 1e6 })} />
              <NumberField label="Ganancia TX · dBi" value={radio.tx_gain_dbi} min={-100} max={100} onChange={n => n !== null && editRadio({ tx_gain_dbi: n })} />
              <NumberField label="Ganancia RX · dBi" value={radio.rx_gain_dbi} min={-100} max={100} onChange={n => n !== null && editRadio({ rx_gain_dbi: n })} />
              <NumberField label="Ruido receptor · dB" value={radio.noise_figure_db} min={0} max={60} onChange={n => n !== null && editRadio({ noise_figure_db: n })} />
            </div>
            <p className="helper">Configurar un protocolo no verifica las funciones del producto. Las tecnologías se evaluarán por separado.</p>
            <h3>Conexiones</h3><label className="field"><span>Añadir enlace con</span><select value="" onChange={e => {
              const targetId = e.target.value; if (!targetId) return;
              change(p => { const target = p.devices.find(d => d.id === targetId)!; p.links.push({ id: crypto.randomUUID(), source_device_id: device.id,
                source_radio_id: radio.id, target_device_id: target.id, target_radio_id: target.radios[0].id }); });
            }}><option value="">Seleccionar equipo…</option>{project?.devices.filter(d => d.id !== device.id).map(d => <option key={d.id} value={d.id}>{d.name} · {d.radios[0].id}</option>)}</select></label>
            <button className="danger-link" onClick={() => { change(p => { p.devices = p.devices.filter(d => d.id !== device.id); p.links = p.links.filter(l => l.source_device_id !== device.id && l.target_device_id !== device.id); }); setSelected(''); }}>Eliminar dispositivo y sus enlaces</button>
          </> : <p className="helper">Selecciona una pared o un dispositivo para editar sus propiedades.</p>}</>}
        </aside>
      </section>

      <section className="results-panel panel">
        <div className="results-heading"><div><span className="eyebrow">DIAGNÓSTICO DE LA INSTALACIÓN</span><h2>Comprueba cada dirección.</h2></div>
          {result && <button onClick={() => download({ project, result }, 'diagnostico.json')}>Exportar diagnóstico</button>}</div>
        {result ? <>
          <div className="result-meta"><span>{result.links.length} enlaces evaluados</span><span>{result.elapsed_ms.toFixed(1)} ms</span>
            <span title={result.input_hash}>Escenario {result.input_hash.slice(0, 10)}</span><span>Modelo {result.engine_version} · sin calibrar</span></div>
          <div className="table-scroll"><table><thead><tr><th>Enlace</th><th>Ida · dBm</th><th>Vuelta · dBm</th><th>Margen ida / vuelta · dB</th><th>Evaluación</th></tr></thead><tbody>
            {result.links.map(link => {
              const configured = project?.links.find(l => l.id === link.id);
              const name = (id: string | undefined) => project?.devices.find(d => d.id === id)?.name ?? id;
              const n = (v: number | null | undefined) => v == null ? 'Sin datos' : v.toFixed(1);
              return <tr key={link.id}><td><strong>{name(configured?.source_device_id)} ↔ {name(configured?.target_device_id)}</strong>
                {link.reasons.length > 0 && <details><summary>Ver diagnóstico</summary>{link.reasons.map((reason, i) => <p key={i}>{reason}</p>)}</details>}</td>
                <td>{n(link.forward?.received_power_dbm)}</td><td>{n(link.reverse?.received_power_dbm)}</td>
                <td>{n(link.forward?.margin_db)} / {n(link.reverse?.margin_db)}</td><td><span className={`badge ${link.status}`}>{statusNames[link.status]}</span></td></tr>;
            })}
          </tbody></table></div>
          <details className="limitations"><summary>Alcance y límites de esta estimación</summary><p>{result.scope}</p><ul>{result.limitations.map(l => <li key={l}>{l}</li>)}</ul></details>
        </> : <div className="results-empty"><span>↗</span><div><strong>{project?.links.length ? 'Tu escenario está listo para explorar.' : 'Añade dispositivos y conecta los que quieras evaluar.'}</strong>
          <p>Ejecuta una estimación para ver señal y margen en ambos sentidos. La velocidad real y la latencia requieren simulación de tráfico.</p></div></div>}
      </section>
      {!!project?.migration_notes.length && <details className="migration panel"><summary>Datos importados · {project.migration_notes.length} notas que debes revisar</summary>
        <ul>{project.migration_notes.map(note => <li key={note}>{note}</li>)}</ul></details>}
      <footer className="app-footer">Smart Environment <span>Una estimación orienta el diseño. Las mediciones permiten validarlo.</span></footer>
    </main>
  </div>;
}
