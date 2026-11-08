import { useEffect, useRef, useState } from 'react';
import { api } from './api';
import type { Radio } from './generated/project';
import type { GenericProfile } from './generated/radio-profile';
import type { ReceiverProfile } from './generated/coverage-map';
import { profileReceiver, provenanceNames } from './editor/radioProfiles';

export default function GenericProfilePicker({ apRadio, onChange }: { apRadio: Radio | undefined; onChange: (profile: ReceiverProfile | null) => void }) {
  const [profiles, setProfiles] = useState<GenericProfile[]>([]), [loadError, setLoadError] = useState(''), [attempt, setAttempt] = useState(0);
  const [id, setId] = useState(''), [tx, setTX] = useState(''), [source, setSource] = useState(''), [provenance, setProvenance] = useState<'declared' | 'measured'>('declared');
  const [txInvalid, setTXInvalid] = useState(false);
  const [error, setError] = useState(''); const changeRef = useRef(onChange); changeRef.current = onChange;
  useEffect(() => { let active = true; setLoadError('');
    void api<GenericProfile[]>('/profiles').then(values => { if (active) setProfiles(values); }).catch(e => { if (active) setLoadError(String(e)); });
    return () => { active = false; }; }, [attempt]);
  const profile = profiles.find(item => item.id === id), radioKey = JSON.stringify(apRadio);
  useEffect(() => {
    try {
      if (!profile || !apRadio) { changeRef.current(null); setError(''); return; }
      if (txInvalid || (tx.trim() && !Number.isFinite(Number(tx)))) throw new Error('La potencia TX debe ser un número finito entre −100 y 100 dBm.');
      const receiver = profileReceiver(profile, apRadio, tx.trim() ? { value: Number(tx), provenance, source: source.trim() } : null);
      changeRef.current(receiver); setError('');
    } catch (e) { changeRef.current(null); setError(e instanceof Error ? e.message : String(e)); }
  }, [profile, radioKey, tx, source, provenance, txInvalid]);
  return <div className="generic-profile">
    <p className="helper">Perfiles genéricos preliminares, sin equivalencia con un producto. La tabla HT de 2,4 GHz está pendiente de cotejo; revisa las notas y procedencia antes de interpretar el mapa.</p>
    {loadError ? <p className="message error" role="alert">No se pudieron cargar perfiles: {loadError} <button type="button" onClick={() => setAttempt(value => value + 1)}>Reintentar perfiles</button></p>
      : <label className="field"><span>Perfil Wi-Fi genérico</span><select aria-label="Perfil Wi-Fi genérico" value={id} onChange={event => { setId(event.target.value); setTX(''); setSource(''); setTXInvalid(false); }}>
        <option value="">Seleccionar perfil…</option>{profiles.map(item => <option key={item.id} value={item.id}>{item.name} · {item.mode}</option>)}
      </select></label>}
    {profile && <><p className="helper">{profile.description}</p>
      <div className="table-scroll"><table><caption>Valores del catálogo; la TX opcional de abajo los completa.</caption><thead><tr><th>Parámetro</th><th>Valor</th><th>Procedencia</th><th>Fuente</th></tr></thead><tbody>
        {[[ 'Sensibilidad · dBm', profile.sensitivity_dbm ], [ 'Potencia TX · dBm', profile.tx_power_dbm ],
          [ 'Ganancia · dBi', profile.antenna_gain_dbi ], [ 'Figura de ruido · dB', profile.noise_figure_db ]].map(([name, raw]) => {
            const value = raw as GenericProfile['sensitivity_dbm']; return <tr key={String(name)}><td>{String(name)}</td><td>{value.value ?? 'Desconocido'}</td><td>{provenanceNames[value.provenance]}</td><td>{value.source ?? 'Sin fuente'}</td></tr>;
          })}</tbody></table></div>
      <ul className="helper">{profile.notes.map((note, index) => <li key={index}>{note}</li>)}</ul>
      <div className="analysis-fields"><label className="field"><span>TX conocida del cliente · dBm (opcional)</span><input aria-label="TX conocida del cliente · dBm" type="number" min={-100} max={100} step="any" value={tx} aria-invalid={txInvalid}
        onChange={event => { setTX(event.target.value); setTXInvalid(event.target.validity.badInput || event.target.validity.rangeOverflow || event.target.validity.rangeUnderflow); }} /></label>
        <label className="field"><span>Procedencia de la TX</span><select aria-label="Procedencia de la TX" value={provenance} onChange={event => setProvenance(event.target.value as typeof provenance)}><option value="declared">Declarada</option><option value="measured">Medida</option></select></label>
        <label className="field"><span>Fuente de la TX del cliente</span><input aria-label="Fuente de la TX del cliente" value={source} maxLength={500} onChange={event => setSource(event.target.value)} /></label></div>
      <p className="helper">Dejar TX vacía conserva el dato desconocido y la vuelta sin calcular. El perfil sigue el canal del AP; no se modifican los equipos del proyecto.</p>
    </>}
    {error && <p role="alert" className="message error">{error}</p>}
  </div>;
}
