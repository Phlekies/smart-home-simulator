import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import type { Material } from './generated/project';
import { makeMaterialRange } from './editor/uncertainty';

export default function MaterialUncertaintyEditor({ material, wallCount, onEdit }: {
  material: Material; wallCount: number; onEdit: (patch: Partial<Material>) => void;
}) {
  const [values, setValues] = useState<string[]>([]), [source, setSource] = useState(''), [error, setError] = useState('');
  const [editing, setEditing] = useState(false);
  const savedKey = JSON.stringify(material);
  useEffect(() => {
    const r = material.uncertainty;
    setValues([r?.loss_db_24ghz_low ?? material.loss_db_24ghz, r?.loss_db_24ghz_high ?? material.loss_db_24ghz,
      r?.loss_db_5ghz_low ?? material.loss_db_5ghz, r?.loss_db_5ghz_high ?? material.loss_db_5ghz].map(String));
    setSource(r?.source ?? ''); setEditing(false); setError('');
  }, [savedKey]);
  function apply(event: FormEvent) {
    event.preventDefault();
    try { onEdit({ uncertainty: makeMaterialRange(material, values, source) }); setEditing(false); setError(''); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  return <details className="material-details"><summary>Incertidumbre del material</summary>
    <p className="helper">Afecta a {wallCount} paredes de {material.name}. Son límites de escenario razonados, sin probabilidad asociada. La pérdida nominal debe quedar dentro de cada rango.</p>
    <p className="helper">Nominal: {material.loss_db_24ghz} dB a 2,4 GHz · {material.loss_db_5ghz} dB a 5 GHz. Declarar el rango de 5 GHz no valida esa banda.</p>
    <form onSubmit={apply} noValidate>
      <div className="radio-fields">{['Mínimo 2,4 GHz · dB', 'Máximo 2,4 GHz · dB', 'Mínimo 5 GHz · dB', 'Máximo 5 GHz · dB'].map((label, index) =>
        <label className="field" key={label}><span>{label}</span><input aria-label={label} type="number" min={0} max={1000} step="any" value={values[index] ?? ''}
          onChange={event => { setValues(previous => previous.map((value, i) => i === index ? event.target.value : value)); setEditing(true); }} /></label>)}</div>
      <label className="field"><span>Fuente o motivo del rango</span><input aria-label="Fuente o motivo del rango" value={source} maxLength={500}
        onChange={event => { setSource(event.target.value); setEditing(true); }} /></label>
      <button type="submit">Aplicar rango del material</button>
      {editing && <p className="helper" role="status">Rango pendiente de aplicar; el proyecto conserva los valores anteriores.</p>}
      {error && <p role="alert" className="message error">{error}</p>}
    </form>
    {material.uncertainty && <><p className="helper">Fuente guardada: {material.uncertainty.source}</p>
      <button type="button" onClick={() => onEdit({ uncertainty: null })}>Retirar rango del material</button></>}
  </details>;
}
