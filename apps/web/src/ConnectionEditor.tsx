import { useId, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import type { Device, Project, Radio } from './generated/project';
import { hasRadioConnection, MAX_LINKS } from './editor/connections';

const pair = (deviceId: string, radioId: string) => JSON.stringify([deviceId, radioId]);
const describe = (radio: Radio) => `${radio.id} · ${radio.protocol === 'unknown' ? 'protocolo por verificar' : radio.protocol.toUpperCase()} · ${radio.frequency_hz / 1e6} MHz`;

export default function ConnectionEditor({ project, device, radio, disabled, onAdd, onRemove }: {
  project: Project; device: Device; radio: Radio; disabled: boolean;
  onAdd: (deviceId: string, radioId: string) => string | null;
  onRemove: (id: string) => string | null;
}) {
  const [target, setTarget] = useState('');
  const [error, setError] = useState('');
  const input = useRef<HTMLSelectElement>(null);
  const errorId = useId();
  const otherDevices = project.devices.filter(other => other.id !== device.id);
  const attached = project.links.filter(link => link.source_device_id === device.id || link.target_device_id === device.id);
  const hasAvailableTarget = otherDevices.some(other => other.radios.some(otherRadio => !hasRadioConnection(project,
    { source_device_id: device.id, source_radio_id: radio.id, target_device_id: other.id, target_radio_id: otherRadio.id })));

  function add(event: FormEvent) {
    event.preventDefault(); if (disabled) return;
    const chosen = otherDevices.flatMap(other => other.radios.map(otherRadio => ({ device: other, radio: otherRadio })))
      .find(option => pair(option.device.id, option.radio.id) === target);
    if (!chosen) { setError('Selecciona una radio de destino de otro equipo.'); input.current?.focus(); return; }
    const problem = onAdd(chosen.device.id, chosen.radio.id);
    setError(problem ?? '');
    if (problem) return;
    setTarget(''); input.current?.focus();
  }
  function remove(id: string) {
    const problem = onRemove(id); setError(problem ?? '');
    if (!problem) window.requestAnimationFrame(() => input.current?.focus());
  }
  return <section className="connection-editor" aria-label="Conexiones del equipo">
    <h3>Conexiones <small>{attached.length} del equipo</small></h3>
    <p className="helper">Radio emisora: {describe(radio)}. Un enlace evalúa las dos direcciones; no acredita conexión a Internet ni funcionamiento de una malla.</p>
    <form onSubmit={add} noValidate><fieldset className="inspector-fields" disabled={disabled || project.links.length >= MAX_LINKS}>
      <legend className="sr-only">Añadir enlace desde {radio.id}</legend>
      <label className="field"><span>Radio de destino</span><select ref={input} value={target} required aria-invalid={Boolean(error)} aria-describedby={error ? errorId : undefined}
        onChange={e => { setTarget(e.target.value); setError(''); }}>
        <option value="">Seleccionar equipo y radio…</option>
        {otherDevices.map(other => <optgroup key={other.id} label={other.name}>{other.radios.map(otherRadio => {
          const exists = hasRadioConnection(project, { source_device_id: device.id, source_radio_id: radio.id, target_device_id: other.id, target_radio_id: otherRadio.id });
          return <option key={otherRadio.id} value={pair(other.id, otherRadio.id)} disabled={exists}>{other.name} · {describe(otherRadio)}{exists ? ' · ya enlazada' : ''}</option>;
        })}</optgroup>)}
      </select></label>
      <button type="submit" disabled={!hasAvailableTarget}>Añadir enlace</button>
    </fieldset></form>
    {!otherDevices.length && <p className="helper">Añade otro equipo para definir un enlace.</p>}
    {otherDevices.length > 0 && !hasAvailableTarget && <p className="helper">Todas las radios de destino ya están enlazadas con esta interfaz.</p>}
    {project.links.length >= MAX_LINKS && <p className="helper">Límite de 512 enlaces alcanzado. Puedes retirar alguno antes de crear otro.</p>}
    {error && <p id={errorId} role="alert" className="field-error">{error}</p>}
    {attached.length > 0 && <ul className="connection-list">{attached.map(link => {
      const source = project.devices.find(other => other.id === link.source_device_id);
      const targetDevice = project.devices.find(other => other.id === link.target_device_id);
      const label = `${source?.name ?? link.source_device_id} (${link.source_radio_id}) ↔ ${targetDevice?.name ?? link.target_device_id} (${link.target_radio_id})`;
      return <li key={link.id}><span>{label}</span><button disabled={disabled} onClick={() => remove(link.id)} aria-label={`Eliminar enlace ${label}`}>Quitar enlace</button></li>;
    })}</ul>}
  </section>;
}
