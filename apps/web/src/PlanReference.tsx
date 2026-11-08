import { useEffect, useRef, useState } from 'react';
import type { ChangeEvent, FormEvent, PointerEvent } from 'react';
import { imageFileError, referenceBounds } from './editor/reference';
import type { PixelPoint } from './editor/reference';
import type { PlanReference as SavedReference } from './generated/project';
import { imageDigest, makeReference, matchesReference } from './editor/referencePersistence';
import type { LocalReferenceImage, ReferenceView } from './editor/referencePersistence';

export default function PlanReference({ saved, image, view, disabled, onImage, onSave, onView }: {
  saved: SavedReference | null; image: LocalReferenceImage | null; view: ReferenceView; disabled: boolean;
  onImage: (image: LocalReferenceImage | null) => void; onSave: (saved: SavedReference | null) => void;
  onView: (view: ReferenceView) => void;
}) {
  const [draft, setDraft] = useState<LocalReferenceImage | null>(null);
  const draftRef = useRef<LocalReferenceImage | null>(null);
  const ownedUrls = useRef(new Set<string>());
  const associated = matchesReference(saved, image);
  const previewImage = draft ?? (associated ? image : null);
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
  const mode = useRef<'associate' | 'replace'>('replace');
  const savedKey = JSON.stringify(saved);
  const currentSavedKey = useRef(savedKey); currentSavedKey.current = savedKey;
  const pairBefore = useRef<{ a: PixelPoint; b: PixelPoint; dirty: boolean } | null>(null);

  function release(url: string) { if (ownedUrls.current.delete(url)) URL.revokeObjectURL(url); }
  function clearDraft() { if (draftRef.current) release(draftRef.current.url); draftRef.current = null; setDraft(null); }
  function hydrate(reference: SavedReference | null) {
    setA(reference?.calibration?.point_a_px ?? { x: 0, y: (reference?.height_px ?? 0) / 2 });
    setB(reference?.calibration?.point_b_px ?? { x: reference?.width_px ?? 0, y: (reference?.height_px ?? 0) / 2 });
    setDistance(reference?.calibration ? String(reference.calibration.distance_m) : '');
    setOriginX(String(reference?.origin_x_m ?? 0)); setOriginY(String(reference?.origin_y_m ?? 0));
    setNextPoint('a'); pairBefore.current = null; setDirty(false);
  }
  useEffect(() => () => { request.current += 1; for (const url of ownedUrls.current) URL.revokeObjectURL(url); ownedUrls.current.clear(); }, []);
  useEffect(() => { request.current += 1; setLoading(false); clearDraft(); hydrate(saved); setError(''); }, [savedKey]);

  function choose(nextMode: 'associate' | 'replace') { mode.current = nextMode; fileInput.current?.click(); }

  async function openImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]; event.target.value = '';
    if (!file) return;
    const problem = imageFileError(file.type, file.size);
    if (problem) { setError(problem); return; }
    const sequence = ++request.current, expectedKey = savedKey, operation = mode.current;
    setLoading(true); setError('');
    const url = URL.createObjectURL(file); ownedUrls.current.add(url);
    try {
      const decoded = new Image(); decoded.src = url; await decoded.decode();
      const widthPx = decoded.naturalWidth, heightPx = decoded.naturalHeight;
      referenceBounds(widthPx, heightPx, { metersPerPixel: .01, originX: 0, originY: 0 });
      const sha256 = await imageDigest(await file.arrayBuffer());
      if (sequence !== request.current || expectedKey !== currentSavedKey.current) { release(url); return; }
      const next: LocalReferenceImage = { url, fileName: file.name, mediaType: file.type as LocalReferenceImage['mediaType'], widthPx, heightPx, sha256 };
      if (operation === 'associate') {
        if (!matchesReference(saved, next)) throw new Error('La imagen no coincide con la huella, dimensiones o tipo del plano guardado. La referencia anterior se conserva.');
        clearDraft(); ownedUrls.current.delete(url); onImage(next); hydrate(saved);
        setMessage('Imagen comprobada y reasociada. Se conservan la escala y el origen guardados.');
      } else {
        clearDraft(); draftRef.current = next; setDraft(next);
        setA({ x: 0, y: heightPx / 2 }); setB({ x: widthPx, y: heightPx / 2 });
        setDistance(''); setOriginX('0'); setOriginY('0'); setNextPoint('a'); setDirty(true); pairBefore.current = null;
        setMessage('Imagen pendiente: indica una distancia conocida y aplica la escala. La referencia guardada se conserva hasta aplicar.');
      }
    } catch (e) {
      release(url);
      if (sequence === request.current) setError(`No se pudo cargar la imagen. ${e instanceof Error ? e.message : 'Comprueba el archivo.'}`);
    } finally { if (sequence === request.current) setLoading(false); }
  }

  function pick(event: PointerEvent<SVGSVGElement>) {
    if (!previewImage || disabled || loading || event.button !== 0 || !event.isPrimary) return;
    const matrix = preview.current?.getScreenCTM(); if (!matrix) return;
    const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
    if (point.x < 0 || point.y < 0 || point.x > previewImage.widthPx || point.y > previewImage.heightPx) return;
    event.currentTarget.focus({ preventScroll: true }); event.preventDefault();
    const chosen = { x: point.x, y: point.y };
    if (nextPoint === 'a') { pairBefore.current = { a, b, dirty }; setA(chosen); setNextPoint('b'); setMessage('Punto A elegido. Selecciona el punto B.'); }
    else { setB(chosen); setNextPoint('a'); pairBefore.current = null; setMessage('Punto B elegido. Indica la distancia real y aplica la escala.'); }
    setDirty(true); setError('');
  }

  function apply(event: FormEvent) {
    event.preventDefault(); if (!previewImage || disabled || loading) return;
    if (nextPoint === 'b') { setError('Completa el punto B o pulsa Escape para cancelar la selección.'); return; }
    try {
      if (originX.trim() === '' || originY.trim() === '') throw new Error('Indica las dos coordenadas del origen.');
      const reference = makeReference(previewImage, a, b, Number(distance), { originX: Number(originX), originY: Number(originY) });
      ownedUrls.current.delete(previewImage.url); onImage(previewImage);
      draftRef.current = null; setDraft(null); onSave(reference);
      setDirty(false); setError(''); setMessage('Escala y origen aplicados al proyecto. Se incluirán en el JSON y en la recuperación local.');
    } catch (e) { setError(e instanceof Error ? e.message : 'Revisa la escala y el origen.'); }
  }

  function pointFields(name: string, point: PixelPoint, update: (point: PixelPoint) => void) {
    return <fieldset className="reference-point"><legend>Punto {name} · píxeles</legend>
      {(['x', 'y'] as const).map(axis => <label className="field" key={axis}><span>{name} · {axis.toUpperCase()} px</span>
        <input type="number" value={point[axis]} min={0} max={axis === 'x' ? previewImage?.widthPx : previewImage?.heightPx} step="any"
          onChange={e => { if (e.target.value === '') return; const number = Number(e.target.value); if (!Number.isFinite(number)) return;
            update({ ...point, [axis]: number }); setNextPoint('a'); pairBefore.current = null; setDirty(true); }} /></label>)}
    </fieldset>;
  }

  return <details className="reference-panel" open aria-busy={loading || disabled}>
    <summary>Plano de referencia · {saved ? associated ? 'escala guardada · imagen disponible' : 'escala guardada · imagen no disponible' : 'sin escala aplicada'}</summary>
    <p className="helper">El JSON y la recuperación conservan escala, origen y calibración. La imagen sigue en tu archivo local: selecciónala de nuevo al abrir. Sus bytes no se envían a la API. Opacidad y visibilidad son de sesión.</p>
    {saved && <div className="helper reference-saved" role="status">
      <p>{associated ? 'Imagen local comprobada.' : 'Imagen no disponible. Reasocia el archivo original para mostrarla con la escala guardada.'}</p>
      <p>{saved.file_name} · {saved.width_px} × {saved.height_px} px · escala {saved.meters_per_pixel} m/px · origen ({saved.origin_x_m}, {saved.origin_y_m}) m.</p>
      <details><summary>Procedencia y huella del archivo</summary><p>{saved.evidence}</p><p style={{ overflowWrap: 'anywhere' }}>SHA-256: {saved.sha256}</p></details>
    </div>}
    <fieldset className="inspector-fields" disabled={loading || disabled}><legend className="sr-only">Referencia de plano</legend>
    <div className="reference-actions">
      {saved && <button type="button" onClick={() => choose('associate')}>Reasociar imagen guardada</button>}
      <button type="button" onClick={() => choose('replace')}>{loading ? 'Leyendo imagen…' : saved || draft ? 'Elegir otra imagen' : 'Cargar imagen de plano'}</button>
      <input ref={fileInput} type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={e => void openImage(e)} />
      <span className="helper">PNG, JPEG o WebP · hasta 8 MB y 16 megapíxeles</span>
      {draft && <button type="button" onClick={() => { clearDraft(); hydrate(saved); setError(''); setMessage('Imagen pendiente descartada. Se conserva la referencia guardada.'); }}>Descartar imagen pendiente</button>}
      {saved && <button type="button" onClick={() => { request.current += 1; clearDraft(); onImage(null); onSave(null); setError(''); setMessage('Referencia retirada del proyecto. Puedes deshacerlo; las paredes se conservan.'); }}>Retirar referencia guardada</button>}
    </div>
    {error && <p className="message error" role="alert">{error}</p>}
    {previewImage && <form className="reference-form" onSubmit={apply}>
      <div className="reference-preview">
        <p className="helper">{previewImage.fileName} · {previewImage.widthPx} × {previewImage.heightPx} px. Próximo clic: punto {nextPoint.toUpperCase()}.</p>
        <svg ref={preview} viewBox={`0 0 ${previewImage.widthPx} ${previewImage.heightPx}`} tabIndex={0}
          aria-label="Calibrar imagen: elige los puntos A y B de una distancia conocida. También puedes introducir las coordenadas en los campos."
          onPointerDown={pick} onKeyDown={e => { if (e.key === 'Escape') {
            if (pairBefore.current) { setA(pairBefore.current.a); setB(pairBefore.current.b); setDirty(pairBefore.current.dirty); pairBefore.current = null; }
            setNextPoint('a'); setError(''); setMessage('Selección cancelada. Puedes empezar de nuevo por el punto A.');
          } }}>
          <image href={previewImage.url} width={previewImage.widthPx} height={previewImage.heightPx} />
          <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#b33224" strokeWidth="3" vectorEffect="non-scaling-stroke" />
          {[{ ...a, label: 'A' }, { ...b, label: 'B' }].map(point => <g key={point.label} transform={`translate(${point.x} ${point.y})`}>
            <circle r={Math.max(previewImage.widthPx, previewImage.heightPx) * .012} fill="#b33224" />
            <text textAnchor="middle" dominantBaseline="central" fontSize={Math.max(previewImage.widthPx, previewImage.heightPx) * .018} fill="white">{point.label}</text>
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
        {dirty && <p className="helper" role="status">Cambios de calibración pendientes de aplicar; aún no se incluyen en el proyecto guardado.</p>}
      </div>
    </form>}
    {saved && associated && <>
      <p className="helper">Imagen aplicada: {(saved.width_px * saved.meters_per_pixel).toFixed(2)} × {(saved.height_px * saved.meters_per_pixel).toFixed(2)} m. Origen = esquina superior izquierda.</p>
      <label className="field"><span>Opacidad del plano · {Math.round(view.opacity * 100)} %</span><input type="range" min=".1" max="1" step=".05" value={view.opacity}
        onChange={e => onView({ ...view, opacity: Number(e.target.value) })} /></label>
      <label className="reference-toggle"><input type="checkbox" checked={view.visible} onChange={e => onView({ ...view, visible: e.target.checked })} /> Mostrar imagen en el plano</label>
    </>}
    </fieldset>
    {message && <p className="helper" role="status">{message}</p>}
  </details>;
}
