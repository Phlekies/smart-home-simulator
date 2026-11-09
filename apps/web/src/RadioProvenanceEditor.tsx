import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { provenanceNames } from './editor/radioProfiles';
import { allowedProvenance, missingRadioValue, radioParameterNames, radioParameters, withRadioProvenance } from './editor/radioProvenance';
import type { RadioParameter } from './editor/radioProvenance';
import type { Radio, RadioValueSource } from './generated/project';
import './radio-provenance.css';

type Props = {
  radio: Radio;
  disabled: boolean;
  onChange: (provenance: Radio['provenance']) => void;
};

function displayedValue(radio: Radio, parameter: RadioParameter) {
  if (missingRadioValue(radio, parameter)) return 'Sin datos';
  const value = radio[parameter];
  const unit = radioParameters[parameter].unit;
  return typeof value === 'string' ? value.toUpperCase() : unit ? `${value} ${unit}` : String(value);
}

function ProvenanceFields({ radio, disabled, onChange, parameter }: Props & { parameter: RadioParameter }) {
  const origin = radio.provenance?.[parameter];
  const savedProvenance = origin?.provenance ?? '';
  const savedSource = origin?.source ?? '';
  const [provenance, setProvenance] = useState<RadioValueSource['provenance'] | ''>(savedProvenance);
  const [source, setSource] = useState(savedSource);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const dirty = provenance !== savedProvenance || (!!provenance && source.trim() !== savedSource);
  const value = radio[parameter];
  useEffect(() => { setProvenance(savedProvenance); setSource(savedSource); setError(''); }, [savedProvenance, savedSource, value]);

  function save(event: FormEvent) {
    event.preventDefault();
    if (disabled || !dirty) return;
    try {
      onChange(withRadioProvenance(radio, parameter, provenance, source));
      setError('');
      setNotice('Se aplicó el cambio de procedencia.');
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : 'No se pudo actualizar la procedencia.');
    }
  }

  return <form onSubmit={save}>
    <fieldset className="inspector-fields" disabled={disabled}>
      <legend className="sr-only">Procedencia de {radioParameters[parameter].label}</legend>
      <label className="field"><span>Origen del valor</span>
        <select value={provenance} onChange={event => {
          const choice = event.target.value as typeof provenance;
          if (choice !== provenance) setSource('');
          setProvenance(choice);
          setError('');
          setNotice('');
        }}>
          <option value="">Sin etiqueta</option>
          {allowedProvenance(radio, parameter).map(kind => <option key={kind} value={kind}>{provenanceNames[kind]}</option>)}
        </select>
      </label>
      <label className="field"><span>Fuente del valor (opcional)</span>
        <input value={source} maxLength={500} disabled={!provenance}
          onChange={event => { setSource(event.target.value); setError(''); setNotice(''); }} />
      </label>
      <button type="submit" aria-disabled={!dirty}>Guardar procedencia</button>
    </fieldset>
    {error && <p className="field-error" role="alert">{error}</p>}
    <span className="sr-only" role="status">{notice}</span>
  </form>;
}

export default function RadioProvenanceEditor(props: Props) {
  const { radio, disabled } = props;
  const [parameter, setParameter] = useState<RadioParameter>('tx_power_dbm');
  return <details className="connection-editor radio-provenance">
    <summary>Procedencia de los datos de radio</summary>
    <p className="helper">Documenta el origen de los valores. Si cambias un valor de radio, su etiqueta se retira para que la fuente anterior no se atribuya al dato nuevo.</p>
    <dl>
      {radioParameterNames.map(name => {
        const entry = radio.provenance?.[name];
        return <div key={name}>
          <dt>{radioParameters[name].label} · {displayedValue(radio, name)}</dt>
          <dd>{entry ? provenanceNames[entry.provenance] : 'Sin etiqueta'}{entry?.source ? ` · ${entry.source}` : ''}</dd>
        </div>;
      })}
    </dl>
    <label className="field"><span>Parámetro que quieres documentar</span>
      <select value={parameter} disabled={disabled} onChange={event => setParameter(event.target.value as RadioParameter)}>
        {radioParameterNames.map(name => <option key={name} value={name}>{radioParameters[name].label}</option>)}
      </select>
    </label>
    <ProvenanceFields key={parameter} {...props} parameter={parameter} />
  </details>;
}
