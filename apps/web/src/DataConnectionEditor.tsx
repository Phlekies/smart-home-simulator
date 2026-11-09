import { useEffect, useId, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { attachedDataLinks, dataConnectionNames, showDataConnection, validatedDataConnection } from './editor/dataConnections';
import type { DataConnectionKind } from './editor/dataConnections';
import type { DataConnection, Device, Project } from './generated/project';

type Props = {
  project: Project;
  device: Device;
  disabled: boolean;
  onChange: (connection: DataConnection | null) => void;
};

function DataConnectionForm({ project, device, disabled, onChange }: Props) {
  const saved = device.data_connection;
  const savedKind = saved?.kind ?? '';
  const savedLink = saved?.link_id ?? '';
  const savedNote = saved?.note ?? '';
  const [kind, setKind] = useState<DataConnectionKind>(savedKind);
  const [linkId, setLinkId] = useState(savedLink);
  const [note, setNote] = useState(savedNote);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const linkInput = useRef<HTMLSelectElement>(null);
  const errorId = useId();
  const attached = attachedDataLinks(project, device.id);
  const chosenLink = attached.some(link => link.id === linkId) ? linkId : '';
  const dirty = kind !== savedKind || (kind === 'wireless' && chosenLink !== savedLink)
    || (!!kind && note.trim() !== savedNote);
  const name = (id: string) => project.devices.find(other => other.id === id)?.name || id;

  useEffect(() => {
    setKind(savedKind);
    setLinkId(savedLink);
    setNote(savedNote);
    setError('');
  }, [savedKind, savedLink, savedNote]);

  function save(event: FormEvent) {
    event.preventDefault();
    if (disabled || !dirty) return;
    try {
      onChange(validatedDataConnection(project, device.id, kind, chosenLink, note));
      setError('');
      setNotice('Se aplicó el cambio de conexión de datos.');
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : 'No se pudo actualizar la conexión.');
      if (kind === 'wireless' && !chosenLink) linkInput.current?.focus();
    }
  }

  return <section className="connection-editor" aria-label="Conexión de datos del equipo">
    <h3>Conexión de datos</h3>
    <p className="helper">Indica cómo llegan los datos de este equipo al router principal. La pasarela y el cable se declaran. La estimación evalúa los enlaces inalámbricos del proyecto en ambos sentidos.</p>
    <p className="helper">Configuración guardada: {dataConnectionNames[saved?.kind ?? 'undefined']}.</p>
    <form onSubmit={save} noValidate>
      <fieldset className="inspector-fields" disabled={disabled}>
        <legend className="sr-only">Configurar conexión de datos</legend>
        <label className="field"><span>Tipo de conexión de datos</span>
          <select value={kind} onChange={event => {
            setKind(event.target.value as DataConnectionKind);
            setError('');
            setNotice('');
          }}>
            <option value="">{dataConnectionNames.undefined}</option>
            {(['gateway', 'wired', 'wireless', 'unknown'] as const).map(option =>
              <option key={option} value={option}>{dataConnectionNames[option]}</option>)}
          </select>
        </label>
        {kind === 'wireless' && <label className="field"><span>Enlace de datos inalámbrico</span>
          <select ref={linkInput} value={chosenLink} required aria-invalid={!!error && !chosenLink}
            aria-describedby={error && !chosenLink ? errorId : undefined} onChange={event => {
              setLinkId(event.target.value);
              setError('');
              setNotice('');
            }}>
            <option value="">Selecciona un enlace…</option>
            {attached.map(link => <option key={link.id} value={link.id}>
              {name(link.source_device_id)} ({link.source_radio_id}) ↔ {name(link.target_device_id)} ({link.target_radio_id})
            </option>)}
          </select>
          {!attached.length && <small>Crea primero un enlace en «Conexiones».</small>}
        </label>}
        {!!kind && <label className="field"><span>Nota sobre la conexión (opcional)</span>
          <input value={note} maxLength={500} onChange={event => { setNote(event.target.value); setError(''); setNotice(''); }} />
        </label>}
        <button type="submit" aria-disabled={!dirty}>Guardar conexión de datos</button>
      </fieldset>
      {error && <p id={errorId} className="field-error" role="alert">{error}</p>}
    </form>
    <span className="sr-only" role="status">{notice}</span>
  </section>;
}

export default function DataConnectionEditor(props: Props) {
  return showDataConnection(props.device) ? <DataConnectionForm key={props.device.id} {...props} /> : null;
}
