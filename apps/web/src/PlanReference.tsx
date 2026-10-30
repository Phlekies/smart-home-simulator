import { useEffect, useRef, useState } from 'react';
import type { ChangeEvent, FormEvent, PointerEvent } from 'react';
import { calibrateReference, imageFileError, referenceBounds } from './editor/reference';
import type { PixelPoint, PlanReference as Reference, ReferencePlacement } from './editor/reference';

type ImageInfo = { url: string; name: string; widthPx: number; heightPx: number };

export default function PlanReference({ value, onChange }: { value: Reference | null; onChange: (value: Reference | null) => void }) {
  const [image, setImage] = useState<ImageInfo | null>(null);
  const [a, setA] = useState<PixelPoint>({ x: 0, y: 0 });
  const [b, setB] = useState<PixelPoint>({ x: 0, y: 0 });
  const [nextPoint, setNextPoint] = useState<'a' | 'b'>('a');
  const [distance, setDistance] = useState('');
  const [originX, setOriginX] = useState('0');
  const [originY, setOriginY] = useState('0');
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const preview = useRef<SVGSVGElement>(null);
  const request = useRef(0);
  const pairBefore = useRef<{ a: PixelPoint; b: PixelPoint; dirty: boolean } | null>(null);

  useEffect(() => () => { request.current += 1; }, []);
  useEffect(() => () => { if (image) URL.revokeObjectURL(image.url); }, [image]);

  async function openImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]; event.target.value = '';
    if (!file) return;
    const problem = imageFileError(file.type, file.size);
    if (problem) { setError(problem); return; }
    const sequence = ++request.current;
    setLoading(true); setError('');
    const url = URL.createObjectURL(file);
    try {
      const decoded = new Image(); decoded.src = url; await decoded.decode();
      if (sequence !== request.current) { URL.revokeObjectURL(url); return; }
      const widthPx = decoded.naturalWidth, heightPx = decoded.naturalHeight;
      // Check decoded dimensions and physical limits before keeping the resource.
      referenceBounds(widthPx, heightPx, { metersPerPixel: .01, originX: 0, originY: 0 });
      setImage({ url, name: file.name, widthPx, heightPx });
      setA({ x: 0, y: heightPx / 2 }); setB({ x: widthPx, y: heightPx / 2 });
      setDistance(''); setOriginX('0'); setOriginY('0'); setNextPoint('a'); setDirty(true); onChange(null);
      pairBefore.current = null;
      setMessage('Selecciona dos puntos de una distancia conocida o escribe sus coordenadas. Después indica la distancia real.');
    } catch (e) {
      URL.revokeObjectURL(url);
      if (sequence === request.current) setError(`No se pudo cargar la imagen. ${e instanceof Error ? e.message : 'Comprueba el archivo.'}`);
    } finally { if (sequence === request.current) setLoading(false); }
  }

  function pick(event: PointerEvent<SVGSVGElement>) {
    if (!image || event.button !== 0 || !event.isPrimary) return;
    const matrix = preview.current?.getScreenCTM(); if (!matrix) return;
    const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
    if (point.x < 0 || point.y < 0 || point.x > image.widthPx || point.y > image.heightPx) return;
    event.currentTarget.focus({ preventScroll: true }); event.preventDefault();
    const chosen = { x: point.x, y: point.y };
    if (nextPoint === 'a') { pairBefore.current = { a, b, dirty }; setA(chosen); setNextPoint('b'); setMessage('Punto A elegido. Selecciona el punto B.'); }
    else { setB(chosen); setNextPoint('a'); pairBefore.current = null; setMessage('Punto B elegido. Indica la distancia real y aplica la escala.'); }
    setDirty(true); setError('');
  }

  function apply(event: FormEvent) {
    event.preventDefault(); if (!image) return;
    if (nextPoint === 'b') { setError('Completa el punto B o pulsa Escape para cancelar la selección.'); return; }
    try {
      const metersPerPixel = calibrateReference(a, b, Number(distance), image.widthPx, image.heightPx);
      if (originX.trim() === '' || originY.trim() === '') throw new Error('Indica las dos coordenadas del origen.');
      const placement: ReferencePlacement = { metersPerPixel, originX: Number(originX), originY: Number(originY) };
      referenceBounds(image.widthPx, image.heightPx, placement);
      onChange({ ...image, placement, visible: value?.visible ?? true, opacity: value?.opacity ?? .55 });
      setDirty(false); setError(''); setMessage('Escala aplicada a la imagen. Las paredes y los equipos existentes conservan sus medidas.');
    } catch (e) { setError(e instanceof Error ? e.message : 'Revisa la escala y el origen.'); }
  }

  function pointFields(name: string, point: PixelPoint, update: (point: PixelPoint) => void) {
    return <fieldset className="reference-point"><legend>Punto {name} · píxeles</legend>
      {(['x', 'y'] as const).map(axis => <label className="field" key={axis}><span>{name} · {axis.toUpperCase()} px</span>
        <input type="number" value={Number(point[axis].toFixed(3))} min={0} max={axis === 'x' ? image?.widthPx : image?.heightPx} step="any"
          onChange={e => { if (e.target.value === '') return; const number = Number(e.target.value); if (!Number.isFinite(number)) return;
            update({ ...point, [axis]: number }); setNextPoint('a'); pairBefore.current = null; setDirty(true); }} /></label>)}
    </fieldset>;
  }

  return <details className="reference-panel" open>
    <summary>Plano de referencia · {value ? 'escala aplicada' : 'sin escala aplicada'}</summary>
    <p className="helper">Imagen de sesión: no se incluye en Guardar JSON ni en la recuperación al recargar. Las paredes que dibujes sí se guardan.</p>
    <div className="reference-actions"><button type="button" disabled={loading} onClick={() => fileInput.current?.click()}>
      {loading ? 'Leyendo imagen…' : image ? 'Cambiar imagen' : 'Cargar imagen de plano'}</button>
      <input ref={fileInput} type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={e => void openImage(e)} />
      <span className="helper">PNG, JPEG o WebP · hasta 8 MB y 16 megapíxeles</span>
      {image && <button type="button" onClick={() => { request.current += 1; setLoading(false); setImage(null); onChange(null); setError(''); setMessage('Referencia retirada. Las paredes se conservan.'); }}>Retirar referencia</button>}
    </div>
    {error && <p className="message error" role="alert">{error}</p>}
    {image && <form className="reference-form" onSubmit={apply}>
      <div className="reference-preview">
        <p className="helper">{image.name} · {image.widthPx} × {image.heightPx} px. Próximo clic: punto {nextPoint.toUpperCase()}.</p>
        <svg ref={preview} viewBox={`0 0 ${image.widthPx} ${image.heightPx}`} tabIndex={0}
          aria-label="Calibrar imagen: elige los puntos A y B de una distancia conocida. También puedes introducir las coordenadas en los campos."
          onPointerDown={pick} onKeyDown={e => { if (e.key === 'Escape') {
            if (pairBefore.current) { setA(pairBefore.current.a); setB(pairBefore.current.b); setDirty(pairBefore.current.dirty); pairBefore.current = null; }
            setNextPoint('a'); setError(''); setMessage('Selección cancelada. Puedes empezar de nuevo por el punto A.');
          } }}>
          <image href={image.url} width={image.widthPx} height={image.heightPx} />
          <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#b33224" strokeWidth="3" vectorEffect="non-scaling-stroke" />
          {[{ ...a, label: 'A' }, { ...b, label: 'B' }].map(point => <g key={point.label} transform={`translate(${point.x} ${point.y})`}>
            <circle r={Math.max(image.widthPx, image.heightPx) * .012} fill="#b33224" />
            <text textAnchor="middle" dominantBaseline="central" fontSize={Math.max(image.widthPx, image.heightPx) * .018} fill="white">{point.label}</text>
          </g>)}
        </svg>
      </div>
      <div className="reference-controls">
        <div className="reference-points">{pointFields('A', a, setA)}{pointFields('B', b, setB)}</div>
        <label className="field"><span>Distancia real A–B · m</span><input type="number" value={distance} min=".01" max="20000" step="any" required
          onChange={e => { setDistance(e.target.value); setDirty(true); }} /></label>
        <div className="radio-fields"><label className="field"><span>Origen de imagen X · m</span><input type="number" value={originX} min="-10000" max="10000" step="any" required onChange={e => { setOriginX(e.target.value); setDirty(true); }} /></label>
          <label className="field"><span>Origen de imagen Y · m</span><input type="number" value={originY} min="-10000" max="10000" step="any" required onChange={e => { setOriginY(e.target.value); setDirty(true); }} /></label></div>
        <button type="submit" className="primary" disabled={nextPoint === 'b'}>Aplicar escala al plano</button>
        {dirty && <p className="helper">Cambios de calibración pendientes de aplicar.</p>}
        {value && <>
          <p className="helper">Imagen aplicada: {(image.widthPx * value.placement.metersPerPixel).toFixed(2)} × {(image.heightPx * value.placement.metersPerPixel).toFixed(2)} m. Origen = esquina superior izquierda.</p>
          <label className="field"><span>Opacidad del plano · {Math.round(value.opacity * 100)} %</span><input type="range" min=".1" max="1" step=".05" value={value.opacity}
            onChange={e => onChange({ ...value, opacity: Number(e.target.value) })} /></label>
          <label className="reference-toggle"><input type="checkbox" checked={value.visible} onChange={e => onChange({ ...value, visible: e.target.checked })} /> Mostrar imagen en el plano</label>
        </>}
      </div>
    </form>}
    {message && <p className="helper" role="status">{message}</p>}
  </details>;
}
