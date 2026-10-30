import { useId, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import type { Point } from './generated/project';
import { wallPoints } from './editor/wallCreation';

const labels = ['Inicio X · m', 'Inicio Y · m', 'Fin X · m', 'Fin Y · m'];

export default function WallCreator({ onCreate, disabled }: {
  onCreate: (start: Point, end: Point) => void; disabled: boolean;
}) {
  const [coordinates, setCoordinates] = useState(['0', '0', '1', '0']);
  const [invalid, setInvalid] = useState<number[]>([]);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const inputs = useRef<(HTMLInputElement | null)[]>([]);
  const errorId = useId();

  function fail(message: string, fields: number[]) {
    setError(message); setInvalid(fields); setMessage(''); inputs.current[fields[0]]?.focus();
  }
  function create(event: FormEvent) {
    event.preventDefault(); if (disabled) return;
    const values = coordinates.map(Number);
    const bad = coordinates.flatMap((raw, index) => raw.trim() === '' || !Number.isFinite(values[index]) || Math.abs(values[index]) > 10_000 ? [index] : []);
    if (bad.length) { fail('Completa las coordenadas con números entre −10000 y 10000 m.', bad); return; }
    try {
      const [start, end] = wallPoints(values[0], values[1], values[2], values[3]);
      onCreate(start, end);
      setError(''); setInvalid([]); setMessage('Pared creada. Puedes ajustar sus propiedades o introducir otra pared.');
    } catch (e) {
      fail(e instanceof Error ? e.message : 'No se pudo crear la pared. Revisa sus coordenadas.', [2, 3]);
    }
  }

  return <details className="wall-creator">
    <summary>Crear pared por coordenadas</summary>
    <p className="helper">Introduce el inicio y el fin en metros. Se conservan tus decimales, sin ajuste a la cuadrícula. Longitud mínima: 0,1 m.</p>
    <form noValidate onSubmit={create}>
      <fieldset className="inspector-fields" disabled={disabled}>
        <legend className="sr-only">Coordenadas de la nueva pared</legend>
        <div className="radio-fields">{labels.map((label, index) => <label className="field" key={label}>
          <span>{label}</span><input ref={element => { inputs.current[index] = element; }}
            type="number" min="-10000" max="10000" step="any" required value={coordinates[index]}
            aria-invalid={invalid.includes(index) || undefined} aria-describedby={invalid.includes(index) ? errorId : undefined}
            onChange={event => {
              setCoordinates(previous => previous.map((value, i) => i === index ? event.target.value : value));
              setError(''); setInvalid([]); setMessage('');
            }} />
        </label>)}</div>
        <button className="primary" type="submit">Crear pared</button>
      </fieldset>
    </form>
    {error && <p id={errorId} className="message error" role="alert">{error}</p>}
    {message && <p className="helper" role="status">{message}</p>}
  </details>;
}
