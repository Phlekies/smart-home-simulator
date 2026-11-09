import { useEffect, useId, useRef, useState } from 'react';
import type { KeyboardEvent, PointerEvent } from 'react';
import type { Point, Project } from './generated/project';
import type { SimulationResult } from './generated/simulation-result';
import { referenceBounds } from './editor/reference';
import type { PlanReference } from './editor/reference';
import type { CoverageLayer } from './editor/coverage';
import { mapExtent, metricNames } from './editor/coverage';
import { doorNames } from './editor/uncertainty';
import { downloadBlob } from './editor/files';
import { createPlanImage } from './editor/planImage';
import { panView, visibleBounds, zoomView } from './editor/viewport';
import type { Bounds, View } from './editor/viewport';

type Pan = { pointerId: number; clientX: number; clientY: number; view: View; worldPerPixel: number };
type Drag = {
  kind: 'device' | 'wall'; id: string; pointerId: number; anchor: Point;
  x: number; y: number; minX: number; minY: number; maxX: number; maxY: number;
  appliedX: number; appliedY: number; started: boolean;
};
const snap = (n: number) => Math.round(n * 10) / 10;
const clamp = (n: number, min = -10000, max = 10000) => Math.max(min, Math.min(max, n));
const planMetres = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 3 });

export default function Plan({ project, selected, onSelect, onMove, result, tool, selectedWallId, reference, coverageLayer,
  onSelectWall, onAddWall, onMoveWall, onGestureStart, onGestureEnd }: {
  project: Project; selected: string; onSelect: (id: string) => void;
  onMove: (id: string, x: number, y: number) => void; result: SimulationResult | null;
  tool: 'select' | 'wall'; selectedWallId: string | null;
  reference: PlanReference | null;
  coverageLayer: CoverageLayer | null;
  onSelectWall: (id: string) => void; onAddWall: (start: Point, end: Point) => void;
  onMoveWall: (id: string, dx: number, dy: number) => void;
  onGestureStart: () => void; onGestureEnd: () => void;
}) {
  const svgRef = useRef<SVGSVGElement>(null);
  const mapClipId = useId();
  const drag = useRef<Drag | null>(null);
  const [frozenBounds, setFrozenBounds] = useState<Bounds | null>(null);
  const [drawingStart, setDrawingStart] = useState<Point | null>(null);
  const [drawingEnd, setDrawingEnd] = useState<Point | null>(null);
  const [drawingMessage, setDrawingMessage] = useState('');
  const [view, setView] = useState<View | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState('');
  const exportPending = useRef(false);
  const latestExport = useRef({ project, coverageLayer, reference });
  latestExport.current = { project, coverageLayer, reference };
  const pan = useRef<Pan | null>(null);
  const endGesture = useRef(onGestureEnd);
  endGesture.current = onGestureEnd;
  const allX = project.devices.map(d => d.position.x).concat(project.building.walls.flatMap(w => [w.start.x, w.end.x]));
  const allY = project.devices.map(d => d.position.y).concat(project.building.walls.flatMap(w => [w.start.y, w.end.y]));
  const imageBounds = reference?.visible ? referenceBounds(reference.widthPx, reference.heightPx, reference.placement) : null;
  const calibration = reference?.visible ? reference.calibration : null;
  if (imageBounds) { allX.push(imageBounds.minX, imageBounds.maxX); allY.push(imageBounds.minY, imageBounds.maxY); }
  const mapGrid = coverageLayer ? mapExtent(coverageLayer.result) : null;
  if (mapGrid) { allX.push(mapGrid.x, mapGrid.x + mapGrid.width); allY.push(mapGrid.y, mapGrid.y + mapGrid.height); }
  const liveBounds = { minX: Math.min(0, ...allX) - 2, minY: Math.min(0, ...allY) - 2,
    maxX: Math.max(project.building.width_m, ...allX) + 2, maxY: Math.max(project.building.depth_m, ...allY) + 2 };
  const bounds = frozenBounds ?? liveBounds;
  const visible = visibleBounds(bounds, view);
  const boundsRef = useRef(bounds); boundsRef.current = bounds;

  useEffect(() => {
    // Ctrl/Cmd + wheel zooms around the pointer; a plain wheel keeps scrolling the page.
    const svg = svgRef.current;
    if (!svg) return;
    function wheel(event: WheelEvent) {
      if (!event.ctrlKey && !event.metaKey) return;
      event.preventDefault();
      const matrix = svgRef.current?.getScreenCTM();
      const at = matrix ? new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse()) : undefined;
      setView(current => zoomView(boundsRef.current, current, event.deltaY < 0 ? 1.25 : 1 / 1.25, at && { x: at.x, y: at.y }));
    }
    svg.addEventListener('wheel', wheel, { passive: false });
    return () => svg.removeEventListener('wheel', wheel);
  }, []);
  function startPan(event: PointerEvent<SVGSVGElement>) {
    const svg = svgRef.current;
    if (!svg || !view) return false;
    const width = svg.getBoundingClientRect().width || 1;
    pan.current = { pointerId: event.pointerId, clientX: event.clientX, clientY: event.clientY, view,
      worldPerPixel: (visible.maxX - visible.minX) / width };
    svg.setPointerCapture(event.pointerId); event.preventDefault();
    return true;
  }
  async function exportImage() {
    const svg = svgRef.current;
    if (!svg || exportPending.current) return;
    const snapshot = latestExport.current;
    const apId = snapshot.coverageLayer?.result.parameters.access_point_device_id;
    const apName = snapshot.project.devices.find(device => device.id === apId)?.name;
    exportPending.current = true;
    setExporting(true);
    setExportMessage('Preparando la imagen…');
    try {
      const { blob, width, height } = await createPlanImage(svg, liveBounds, snapshot.project.name, snapshot.coverageLayer, apName);
      if (svgRef.current !== svg) return;
      const current = latestExport.current;
      if (current.project !== snapshot.project || current.coverageLayer !== snapshot.coverageLayer
        || JSON.stringify(current.reference) !== JSON.stringify(snapshot.reference)) {
        throw new Error('El plano o el mapa cambió durante la exportación. Vuelve a preparar la imagen.');
      }
      const slug = snapshot.project.name.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '');
      downloadBlob(blob, `${slug || 'plano'}.png`);
      setExportMessage(`Imagen del plano completo exportada (${width} × ${height} px).`);
    } catch (e) {
      if (svgRef.current === svg) setExportMessage(`No se pudo exportar la imagen. ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      exportPending.current = false;
      if (svgRef.current === svg) setExporting(false);
    }
  }

  useEffect(() => { setDrawingStart(null); setDrawingEnd(null); setDrawingMessage(''); setFrozenBounds(null); }, [tool]);
  useEffect(() => () => { if (drag.current?.started) endGesture.current(); }, []);
  function position(event: { clientX: number; clientY: number }): Point | null {
    const matrix = svgRef.current?.getScreenCTM();
    if (!matrix) return null;
    const p = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
    return { x: clamp(snap(p.x)), y: clamp(snap(p.y)), z: 0 };
  }
  function finishDrag() {
    if (pan.current) {
      if (svgRef.current?.hasPointerCapture(pan.current.pointerId)) svgRef.current.releasePointerCapture(pan.current.pointerId);
      pan.current = null;
    }
    const current = drag.current;
    drag.current = null;
    if (!drawingStart) setFrozenBounds(null);
    if (current?.started) onGestureEnd();
    if (current && svgRef.current?.hasPointerCapture(current.pointerId)) svgRef.current.releasePointerCapture(current.pointerId);
  }
  function startDrag(event: PointerEvent<SVGGElement>, kind: Drag['kind'], id: string) {
    if (tool !== 'select' || event.button !== 0 || drag.current) return;
    const anchor = position(event);
    if (!anchor) return;
    event.stopPropagation(); event.preventDefault();
    const device = project.devices.find(d => d.id === id);
    const wall = project.building.walls.find(w => w.id === id);
    if (kind === 'device' && device) {
      onSelect(id);
      drag.current = { kind, id, pointerId: event.pointerId, anchor, x: device.position.x, y: device.position.y,
        minX: device.position.x, maxX: device.position.x, minY: device.position.y, maxY: device.position.y,
        appliedX: 0, appliedY: 0, started: false };
    } else if (kind === 'wall' && wall) {
      onSelectWall(id);
      drag.current = { kind, id, pointerId: event.pointerId, anchor, x: wall.start.x, y: wall.start.y,
        minX: Math.min(wall.start.x, wall.end.x), maxX: Math.max(wall.start.x, wall.end.x),
        minY: Math.min(wall.start.y, wall.end.y), maxY: Math.max(wall.start.y, wall.end.y),
        appliedX: 0, appliedY: 0, started: false };
    }
    if (drag.current) { setFrozenBounds(liveBounds); svgRef.current?.setPointerCapture(event.pointerId); }
  }
  function move(event: PointerEvent<SVGSVGElement>) {
    const panning = pan.current;
    if (panning && event.pointerId === panning.pointerId) {
      setView(panView(bounds, panning.view, -(event.clientX - panning.clientX) * panning.worldPerPixel,
        -(event.clientY - panning.clientY) * panning.worldPerPixel));
      return;
    }
    const point = position(event);
    if (!point) return;
    if (tool === 'wall' && drawingStart) setDrawingEnd(point);
    const current = drag.current;
    if (!current || event.pointerId !== current.pointerId) return;
    const dx = clamp(snap(point.x - current.anchor.x), -10000 - current.minX, 10000 - current.maxX);
    const dy = clamp(snap(point.y - current.anchor.y), -10000 - current.minY, 10000 - current.maxY);
    if (dx === current.appliedX && dy === current.appliedY) return;
    if (!current.started) { onGestureStart(); current.started = true; }
    if (current.kind === 'device') onMove(current.id, current.x + dx, current.y + dy);
    else onMoveWall(current.id, dx - current.appliedX, dy - current.appliedY);
    current.appliedX = dx; current.appliedY = dy;
  }
  function draw(event: PointerEvent<SVGSVGElement>) {
    // Middle button pans in any tool; in Select, dragging the empty background pans too.
    const background = event.target === event.currentTarget || (event.target as Element).classList?.contains('plan-background');
    if (view && (event.button === 1 || (tool === 'select' && event.button === 0 && background)) && startPan(event)) return;
    if (tool !== 'wall' || event.button !== 0 || !event.isPrimary) return;
    const point = position(event);
    if (!point) return;
    event.currentTarget.focus({ preventScroll: true });
    if (!drawingStart) {
      setFrozenBounds(liveBounds); setDrawingStart(point); setDrawingEnd(point);
      setDrawingMessage('Elige el final de la pared. Escape cancela.');
    } else if (Math.hypot(point.x - drawingStart.x, point.y - drawingStart.y) < .1 - 1e-8) {
      setDrawingMessage('La pared debe medir al menos 0,1 m. Elige otro punto.');
    } else {
      onAddWall(drawingStart, point); setDrawingStart(null); setDrawingEnd(null); setFrozenBounds(null);
      setDrawingMessage('Pared creada. Elige el inicio de otra pared.');
    }
  }
  function keyboardMove(event: KeyboardEvent<SVGGElement>, kind: Drag['kind'], id: string) {
    if (tool !== 'select') return;
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault(); event.stopPropagation();
      if (kind === 'wall') onSelectWall(id); else onSelect(id);
      return;
    }
    const step = event.shiftKey ? 1 : .1;
    const offsets: Record<string, [number, number]> = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
    const offset = offsets[event.key];
    if (!offset) return;
    event.preventDefault(); event.stopPropagation();
    if (kind === 'device') {
      const device = project.devices.find(d => d.id === id);
      if (!device) return;
      onSelect(id); onGestureStart(); onMove(id, clamp(device.position.x + offset[0]), clamp(device.position.y + offset[1]));
    } else {
      const wall = project.building.walls.find(w => w.id === id);
      if (!wall) return;
      const dx = clamp(offset[0], -10000 - Math.min(wall.start.x, wall.end.x), 10000 - Math.max(wall.start.x, wall.end.x));
      const dy = clamp(offset[1], -10000 - Math.min(wall.start.y, wall.end.y), 10000 - Math.max(wall.start.y, wall.end.y));
      onSelectWall(id); onGestureStart(); onMoveWall(id, dx, dy);
    }
    onGestureEnd();
  }
  const previewLength = drawingStart && drawingEnd ? Math.hypot(drawingEnd.x - drawingStart.x, drawingEnd.y - drawingStart.y) : 0;
  const zoomBy = (factor: number) => setView(current => zoomView(bounds, current, factor));
  return <>
    <div className="plan-controls" role="toolbar" aria-label="Vista del plano">
      <button type="button" onClick={() => zoomBy(1.5)} disabled={(view?.scale ?? 1) >= 20} aria-label="Acercar el plano">＋</button>
      <button type="button" onClick={() => zoomBy(1 / 1.5)} disabled={!view} aria-label="Alejar el plano">－</button>
      <button type="button" onClick={() => setView(null)} disabled={!view}>Ver todo</button>
      <button type="button" aria-disabled={exporting || undefined} onClick={() => void exportImage()}>Exportar imagen</button>
      <span className="plan-zoom" role="status">{view ? `Zoom ×${view.scale.toFixed(1)} · arrastra el fondo para desplazar` : 'Plano completo'}{exportMessage ? ` · ${exportMessage}` : ''}</span>
    </div>
    <svg ref={svgRef} className={`plan ${tool === 'wall' ? 'is-drawing' : ''} ${view ? 'is-zoomed' : ''}`} tabIndex={0} role="group"
      aria-label="Plano de la vivienda. Selecciona y arrastra paredes o dispositivos; usa Dibujar pared para crear obstáculos. Más y menos acercan o alejan, 0 muestra todo y las flechas desplazan el plano ampliado."
      viewBox={`${visible.minX} ${visible.minY} ${visible.maxX - visible.minX} ${visible.maxY - visible.minY}`}
      onPointerDown={draw} onPointerMove={move} onPointerUp={finishDrag} onPointerCancel={finishDrag}
      onLostPointerCapture={() => { if (drag.current) finishDrag(); }} onKeyDown={event => {
        if ((event.ctrlKey || event.metaKey) && !event.altKey && ['z', 'y'].includes(event.key.toLowerCase())) {
          finishDrag(); // Complete the current pointer gesture before App navigates its history.
        }
        if (event.target === event.currentTarget && !event.ctrlKey && !event.metaKey && !event.altKey) {
          const step = (visible.maxX - visible.minX) / 10;
          const pans: Record<string, [number, number]> = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
          if (event.key === '+' || event.key === '=') { event.preventDefault(); zoomBy(1.5); return; }
          if (event.key === '-') { event.preventDefault(); zoomBy(1 / 1.5); return; }
          if (event.key === '0') { event.preventDefault(); setView(null); return; }
          if (view && pans[event.key]) { event.preventDefault(); setView(panView(bounds, view, ...pans[event.key])); return; }
        }
        if (event.key === 'Escape') {
          event.preventDefault(); setDrawingStart(null); setDrawingEnd(null); setFrozenBounds(null);
          setDrawingMessage('Dibujo cancelado.'); finishDrag();
        }
      }}>
      <defs><pattern id="grid" width="1" height="1" patternUnits="userSpaceOnUse">
        <path d="M 1 0 L 0 0 0 1" fill="none" stroke="#38534b" strokeWidth=".025" />
      </pattern>{mapGrid && <clipPath id={mapClipId}><rect x={mapGrid.x} y={mapGrid.y} width={mapGrid.width} height={mapGrid.height} /></clipPath>}</defs>
      {reference?.visible && imageBounds && <image href={reference.url} x={imageBounds.minX} y={imageBounds.minY}
        width={imageBounds.maxX - imageBounds.minX} height={imageBounds.maxY - imageBounds.minY}
        opacity={reference.opacity} pointerEvents="none" />}
      {coverageLayer && mapGrid && <image href={coverageLayer.imageUrl} x={mapGrid.x} y={mapGrid.y}
        width={mapGrid.textureWidth} height={mapGrid.textureHeight}
        preserveAspectRatio="none" clipPath={`url(#${mapClipId})`} opacity=".8" style={{ imageRendering: 'pixelated' }} pointerEvents="none" />}
      <rect className="plan-background" x={bounds.minX} y={bounds.minY} width={bounds.maxX - bounds.minX} height={bounds.maxY - bounds.minY} fill="url(#grid)" />
      {imageBounds && <g pointerEvents="none" aria-hidden="true">
        <line x1={imageBounds.minX} y1={imageBounds.minY - .4} x2={imageBounds.maxX} y2={imageBounds.minY - .4} stroke="#dfcfa0" strokeWidth=".04" />
        <text x={(imageBounds.minX + imageBounds.maxX) / 2} y={imageBounds.minY - .6} textAnchor="middle" fontSize=".4" fill="#dfcfa0">
          Imagen · {(imageBounds.maxX - imageBounds.minX).toFixed(2)} m
        </text>
      </g>}
      {project.links.map(link => {
        const a = project.devices.find(d => d.id === link.source_device_id), b = project.devices.find(d => d.id === link.target_device_id);
        if (!a || !b) return null;
        const status = result?.links.find(l => l.id === link.id)?.status;
        return <line key={link.id} x1={a.position.x} y1={a.position.y} x2={b.position.x} y2={b.position.y} pointerEvents="none"
          stroke={status === 'below-threshold' || status === 'incompatible' ? '#f29b88' : status === 'above-threshold' ? '#79d9b2' : '#6e8e83'}
          strokeWidth=".09" strokeDasharray=".3 .2" opacity=".8" />;
      })}
      {project.building.walls.map((wall, index) => <g key={wall.id} role="button" tabIndex={tool === 'select' ? 0 : -1}
        aria-label={`Seleccionar pared ${index + 1}${wall.door ? ` · ${doorNames[wall.door]}` : ''}`} aria-pressed={selectedWallId === wall.id} className="plan-wall"
        onKeyDown={event => keyboardMove(event, 'wall', wall.id)} onPointerDown={event => startDrag(event, 'wall', wall.id)}>
        <line x1={wall.start.x} y1={wall.start.y} x2={wall.end.x} y2={wall.end.y}
          stroke="transparent" strokeWidth="16" vectorEffect="non-scaling-stroke" />
        <circle cx={wall.start.x} cy={wall.start.y} r=".1" fill="transparent" pointerEvents="none" />
        <circle cx={wall.end.x} cy={wall.end.y} r=".1" fill="transparent" pointerEvents="none" />
        <line x1={wall.start.x} y1={wall.start.y} x2={wall.end.x} y2={wall.end.y} pointerEvents="none"
          stroke={selectedWallId === wall.id ? '#f3cf88' : wall.door === 'open' ? '#82d6c8' : wall.door === 'unknown' ? '#ceaeef' : '#abbcae'}
          strokeDasharray={wall.door === 'open' ? '.18 .3' : wall.door === 'unknown' ? '.4 .18' : undefined}
          strokeWidth={Math.max(.17, wall.thickness_m)} strokeLinecap="square" />
        {selectedWallId === wall.id && <text x={(wall.start.x + wall.end.x) / 2} y={(wall.start.y + wall.end.y) / 2 - .35}
          textAnchor="middle" fontSize=".5" fill="#f3cf88" paintOrder="stroke" stroke="#142221" strokeWidth=".15" pointerEvents="none">
          {Math.hypot(wall.end.x - wall.start.x, wall.end.y - wall.start.y).toFixed(2)} m
        </text>}
      </g>)}
      {calibration && <g pointerEvents="none" aria-hidden="true">
        <line x1={calibration.pointA.x} y1={calibration.pointA.y} x2={calibration.pointB.x} y2={calibration.pointB.y}
          stroke="#142221" strokeWidth="4" vectorEffect="non-scaling-stroke" />
        <line x1={calibration.pointA.x} y1={calibration.pointA.y} x2={calibration.pointB.x} y2={calibration.pointB.y}
          stroke="#f3cf88" strokeWidth="2" vectorEffect="non-scaling-stroke" />
        {[calibration.pointA, calibration.pointB].map((point, index) =>
          <circle key={index} cx={point.x} cy={point.y} r=".07" fill="#f3cf88" stroke="#142221" strokeWidth=".04" />)}
        <text x={(calibration.pointA.x + calibration.pointB.x) / 2} y={(calibration.pointA.y + calibration.pointB.y) / 2 - .26}
          textAnchor="middle" fontSize=".4" fill="#f3cf88" paintOrder="stroke" stroke="#142221" strokeWidth=".12">
          A–B · {planMetres.format(calibration.distanceM)} m
        </text>
      </g>}
      {project.devices.map(device => <g key={device.id} transform={`translate(${device.position.x} ${device.position.y})`}
        role="button" tabIndex={tool === 'select' ? 0 : -1} aria-label={`Seleccionar ${device.name}`} className="plan-device"
        onKeyDown={event => keyboardMove(event, 'device', device.id)} onPointerDown={event => startDrag(event, 'device', device.id)}>
        {selected === device.id && <circle r=".72" fill="#79d9b21c" stroke="#79d9b2" strokeWidth=".06" />}
        <circle r=".36" fill={device.role === 'controller' || device.role === 'access-point' ? '#f3b26f' : '#79d9b2'} stroke="#142221" strokeWidth=".09" />
        <text x=".6" y="-.45" fontSize=".5" fill="#e5eae1" paintOrder="stroke" stroke="#142221" strokeWidth=".15" pointerEvents="none">{device.name}</text>
      </g>)}
      {drawingStart && drawingEnd && <g data-plan-draft="" pointerEvents="none">
        <line x1={drawingStart.x} y1={drawingStart.y} x2={drawingEnd.x} y2={drawingEnd.y} stroke="#f3cf88" strokeWidth=".12" strokeDasharray=".25 .15" />
        <circle cx={drawingStart.x} cy={drawingStart.y} r=".16" fill="#f3cf88" />
        <text x={(drawingStart.x + drawingEnd.x) / 2} y={(drawingStart.y + drawingEnd.y) / 2 - .4}
          textAnchor="middle" fill="#f3cf88" fontSize=".55" paintOrder="stroke" stroke="#142221" strokeWidth=".15">{previewLength.toFixed(2)} m</text>
      </g>}
    </svg>
    {coverageLayer && <p className="map-caption"><strong>{metricNames[coverageLayer.metric]}</strong> · AP {project.devices.find(device => device.id === coverageLayer.result.parameters.access_point_device_id)?.name}
      {' · '}Perfil {coverageLayer.result.parameters.profile.name} · {coverageLayer.result.frequency_hz / 1e6} MHz · altura {coverageLayer.result.parameters.grid.height_m} m · celda {coverageLayer.result.parameters.grid.resolution_m} m
      <br />Sin calibración experimental · rayado: datos parciales · gris: sin valor / sin calcular</p>}
    {tool === 'wall' && <p className="drawing-hint" role="status">{drawingMessage || 'Haz clic en el inicio y el final de la pared. Ajuste: 0,1 m. Escape cancela.'}</p>}
  </>;
}
