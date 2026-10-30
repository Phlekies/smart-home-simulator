import type { Link, Project, Radio } from './generated/project';
import type { DirectionResult, LinkResult } from './generated/simulation-result';

const number = (value: number | null | undefined, unit: string) => value == null || !Number.isFinite(value) ? 'Sin datos' : `${value.toFixed(1)} ${unit}`;
const radioDescription = (radio: Radio | undefined) => radio
  ? `${radio.id} · ${radio.protocol === 'unknown' ? 'protocolo sin verificar' : radio.protocol.toUpperCase()} · ${radio.frequency_hz / 1e6} MHz · canal ${radio.channel ?? 'sin datos'}`
  : 'Sin datos';

export default function LinkDiagnostics({ project, configured, result, onSelectWall }: {
  project: Project; configured: Link; result: LinkResult; onSelectWall: (id: string) => void;
}) {
  function direction(title: string, computed: DirectionResult | null, txId: string, txRadioId: string, rxId: string, rxRadioId: string) {
    const tx = project.devices.find(device => device.id === txId), rx = project.devices.find(device => device.id === rxId);
    const txRadio = tx?.radios.find(radio => radio.id === txRadioId), rxRadio = rx?.radios.find(radio => radio.id === rxRadioId);
    return <section className="direction-diagnostic" aria-label={`${title}: ${tx?.name ?? txId} a ${rx?.name ?? rxId}`}>
      <h4>{title} · {tx?.name ?? txId} → {rx?.name ?? rxId}</h4>
      <p>Radio emisora: {radioDescription(txRadio)}.</p>
      <p>Radio receptora: {radioDescription(rxRadio)}. Sensibilidad receptora: {number(rxRadio?.sensitivity_dbm, 'dBm')}.</p>
      {computed ? <>
        <dl className="direction-metrics">
          <div><dt>Distancia 3D</dt><dd>{number(computed.distance_m, 'm')}</dd></div>
          <div><dt>Pérdida de propagación</dt><dd>{number(computed.path_loss_db, 'dB')}</dd></div>
          <div><dt>Pérdida acumulada de paredes</dt><dd>{number(computed.wall_loss_db, 'dB')}</dd></div>
          <div><dt>Señal prevista</dt><dd>{number(computed.received_power_dbm, 'dBm')}</dd></div>
          <div><dt>Ruido del receptor modelado</dt><dd>{number(computed.noise_dbm, 'dBm')}</dd></div>
          <div><dt>SNR previsto</dt><dd>{number(computed.snr_db, 'dB')}</dd></div>
          <div><dt>Margen sobre sensibilidad</dt><dd>{number(computed.margin_db, 'dB')}</dd></div>
        </dl>
        <p><strong>Paredes cruzadas por el trayecto directo: {computed.crossed_wall_ids.length}</strong></p>
        {computed.crossed_wall_ids.length ? <ul className="crossed-walls">{computed.crossed_wall_ids.map(id => {
          const index = project.building.walls.findIndex(wall => wall.id === id), wall = project.building.walls[index];
          const material = project.building.materials.find(material => material.id === wall?.material_id);
          return <li key={id}>{wall ? <>
            <button onClick={() => onSelectWall(id)}>Inspeccionar pared {index + 1} · {material?.name ?? wall.material_id}</button>
            <span>Espesor {number(wall.thickness_m * 100, 'cm')}. Material: {material?.evidence ?? 'Procedencia desconocida'}.</span>
          </> : `Pared ${id}: detalle no disponible.`}</li>;
        })}</ul> : <p>El modelo no detecta cruces de paredes en este trayecto. Esto no demuestra ausencia de otros obstáculos o interferencias.</p>}
      </> : <p className="direction-unavailable">Este sentido no se ha calculado. Los motivos del enlace se muestran más abajo; no se presupone que funcione.</p>}
    </section>;
  }
  return <div className="link-diagnostics">
    <p>Trayecto directo del estimador. Las pérdidas de paredes son un total del modelo; no explican todas las interacciones de radio en la vivienda.</p>
    {direction('Ida', result.forward, configured.source_device_id, configured.source_radio_id, configured.target_device_id, configured.target_radio_id)}
    {direction('Vuelta', result.reverse, configured.target_device_id, configured.target_radio_id, configured.source_device_id, configured.source_radio_id)}
    {result.reasons.length > 0 && <div><h4>Datos pendientes y motivos del enlace</h4><ul>{result.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul></div>}
    <p>El ruido mostrado incluye ruido térmico y figura de ruido del receptor. No se evalúan interferencias, tráfico ni estabilidad. Un margen positivo no garantiza funcionamiento.</p>
  </div>;
}
