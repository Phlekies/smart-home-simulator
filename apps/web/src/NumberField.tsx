import { useEffect, useId, useState } from 'react';

export default function NumberField({ label, value, onChange, min, max, nullable = false, integer = false }: {
  label: string; value: number | null; onChange: (number: number | null) => void;
  min?: number; max?: number; step?: number; nullable?: boolean; integer?: boolean;
}) {
  const id = useId();
  const [draft, setDraft] = useState(value === null ? '' : String(value));
  const [error, setError] = useState('');
  useEffect(() => { setDraft(value === null ? '' : String(value)); setError(''); }, [value]);
  return <label className="field"><span>{label}</span>
    <input type="number" aria-label={label} value={draft} min={min} max={max} step={integer ? 1 : 'any'} required={!nullable}
      placeholder={nullable ? 'Desconocido' : undefined} aria-invalid={Boolean(error)} aria-describedby={error ? id : undefined}
      onChange={event => {
        const raw = event.target.value; setDraft(raw);
        if (raw === '' && !event.target.validity.badInput) {
          if (nullable) { onChange(null); setError(''); }
          else setError('Introduce un valor. El cambio todavía no se ha aplicado.');
          return;
        }
        const number = Number(raw);
        if (integer && !Number.isInteger(number)) { setError('Introduce un número entero. El cambio todavía no se ha aplicado.'); return; }
        if (event.target.validity.badInput || !Number.isFinite(number)
          || (min !== undefined && number < min) || (max !== undefined && number > max)) {
          setError(`Introduce un número${min === undefined ? '' : ` desde ${min}`}${max === undefined ? '' : ` hasta ${max}`}. El cambio todavía no se ha aplicado.`);
          return;
        }
        try { onChange(number); setError(''); }
        catch (e) { setError(`${e instanceof Error ? e.message : 'Geometría no válida.'} El cambio todavía no se ha aplicado.`); }
      }} />
    {error && <small id={id} className="field-error" role="alert">{error}</small>}
  </label>;
}
