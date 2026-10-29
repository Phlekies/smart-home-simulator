import { useEffect, useRef, useState } from 'react';
import type { KeyboardEvent, PointerEvent } from 'react';
import type { Point, Project } from './generated/project';
import type { SimulationResult } from './generated/simulation-result';

type Bounds = { minX: number; minY: number; maxX: number; maxY: number };
type Drag = {
  kind: 'device' | 'wall'; id: string; pointerId: number; anchor: Point;
  x: number; y: number; minX: number; minY: number; maxX: number; maxY: number;
  appliedX: number; appliedY: number; started: boolean;
};
const snap = (n: number) => Math.round(n * 10) / 10;
const clamp = (n: number, min = -10000, max = 10000) => Math.max(min, Math.min(max, n));

export default function Plan({ project, selected, onSelect, onMove, result, tool, selectedWallId,
  onSelectWall, onAddWall, onMoveWall, onGestureStart, onGestureEnd }: {
  project: Project; selected: string; onSelect: (id: string) => void;
  onMove: (id: string, x: number, y: number) => void; result: SimulationResult | null;
  tool: 'select' | 'wall'; selectedWallId: string | null;
  onSelectWall: (id: string) => void; onAddWall: (start: Point, end: Point) => void;
  onMoveWall: (id: string, dx: number, dy: number) => void;
  onGestureStart: () => void; onGestureEnd: () => void;
}) {
  const svgRef = useRef<SVGSVGElement>(null);
  const drag = useRef<Drag | null>(null);
  const [frozenBounds, setFrozenBounds] = useState<Bounds | null>(null);
  const [drawingStart, setDrawingStart] = useState<Point | null>(null);
  const [drawingEnd, setDrawingEnd] = useState<Point | null>(null);
  const [drawingMessage, setDrawingMessage] = useState('');
  const endGesture = useRef(onGestureEnd);
  endGesture.current = onGestureEnd;
  const allX = project.devices.map(d => d.position.x).concat(project.building.walls.flatMap(w => [w.start.x, w.end.x]));
  const allY = project.devices.map(d => d.position.y).concat(project.building.walls.flatMap(w => [w.start.y, w.end.y]));
  const liveBounds = { minX: Math.min(0, ...allX) - 2, minY: Math.min(0, ...allY) - 2,
    maxX: Math.max(project.building.width_m, ...allX) + 2, maxY: Math.max(project.building.depth_m, ...allY) + 2 };
  const bounds = frozenBounds ?? liveBounds;

  useEffect(() => { setDrawingStart(null); setDrawingEnd(null); setDrawingMessage(''); setFrozenBounds(null); }, [tool]);
  useEffect(() => () => { if (drag.current?.started) endGesture.current(); }, []);
  function position(event: { clientX: number; clientY: number }): Point | null {
    const matrix = svgRef.current?.getScreenCTM();
    if (!matrix) return null;
    const p = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
    return { x: clamp(snap(p.x)), y: clamp(snap(p.y)), z: 0 };
  }
  function finishDrag() {
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
  return <>
    <svg ref={svgRef} className={`plan ${tool === 'wall' ? 'is-drawing' : ''}`} tabIndex={0}
      aria-label="Plano de la vivienda. Selecciona y arrastra paredes o dispositivos; usa Dibujar pared para crear obstáculos."
      viewBox={`${bounds.minX} ${bounds.minY} ${bounds.maxX - bounds.minX} ${bounds.maxY - bounds.minY}`}
      onPointerDown={draw} onPointerMove={move} onPointerUp={finishDrag} onPointerCancel={finishDrag}
      onLostPointerCapture={() => { if (drag.current) finishDrag(); }} onKeyDown={event => {
        if ((event.ctrlKey || event.metaKey) && !event.altKey && ['z', 'y'].includes(event.key.toLowerCase())) {
          finishDrag(); // Complete the current pointer gesture before App navigates its history.
        }
        if (event.key === 'Escape') {
          event.preventDefault(); setDrawingStart(null); setDrawingEnd(null); setFrozenBounds(null);
          setDrawingMessage('Dibujo cancelado.'); finishDrag();
        }
      }}>
      <defs><pattern id="grid" width="1" height="1" patternUnits="userSpaceOnUse">
        <path d="M 1 0 L 0 0 0 1" fill="none" stroke="#38534b" strokeWidth=".025" />
      </pattern></defs>
      <rect x={bounds.minX} y={bounds.minY} width={bounds.maxX - bounds.minX} height={bounds.maxY - bounds.minY} fill="url(#grid)" />
      {project.links.map(link => {
        const a = project.devices.find(d => d.id === link.source_device_id), b = project.devices.find(d => d.id === link.target_device_id);
        if (!a || !b) return null;
        const status = result?.links.find(l => l.id === link.id)?.status;
        return <line key={link.id} x1={a.position.x} y1={a.position.y} x2={b.position.x} y2={b.position.y} pointerEvents="none"
          stroke={status === 'below-threshold' || status === 'incompatible' ? '#f29b88' : status === 'above-threshold' ? '#79d9b2' : '#6e8e83'}
          strokeWidth=".09" strokeDasharray=".3 .2" opacity=".8" />;
      })}
      {project.building.walls.map((wall, index) => <g key={wall.id} role="button" tabIndex={tool === 'select' ? 0 : -1}
        aria-label={`Seleccionar pared ${index + 1}`} aria-pressed={selectedWallId === wall.id} className="plan-wall"
        onKeyDown={event => keyboardMove(event, 'wall', wall.id)} onPointerDown={event => startDrag(event, 'wall', wall.id)}>
        <line x1={wall.start.x} y1={wall.start.y} x2={wall.end.x} y2={wall.end.y}
          stroke="transparent" strokeWidth="16" vectorEffect="non-scaling-stroke" />
        <circle cx={wall.start.x} cy={wall.start.y} r=".1" fill="transparent" pointerEvents="none" />
        <circle cx={wall.end.x} cy={wall.end.y} r=".1" fill="transparent" pointerEvents="none" />
        <line x1={wall.start.x} y1={wall.start.y} x2={wall.end.x} y2={wall.end.y} pointerEvents="none"
          stroke={selectedWallId === wall.id ? '#f3cf88' : '#abbcae'} strokeWidth={Math.max(.17, wall.thickness_m)} strokeLinecap="square" />
        {selectedWallId === wall.id && <text x={(wall.start.x + wall.end.x) / 2} y={(wall.start.y + wall.end.y) / 2 - .35}
          textAnchor="middle" fontSize=".5" fill="#f3cf88" paintOrder="stroke" stroke="#142221" strokeWidth=".15" pointerEvents="none">
          {Math.hypot(wall.end.x - wall.start.x, wall.end.y - wall.start.y).toFixed(2)} m
        </text>}
      </g>)}
      {project.devices.map(device => <g key={device.id} transform={`translate(${device.position.x} ${device.position.y})`}
        role="button" tabIndex={tool === 'select' ? 0 : -1} aria-label={`Seleccionar ${device.name}`} className="plan-device"
        onKeyDown={event => keyboardMove(event, 'device', device.id)} onPointerDown={event => startDrag(event, 'device', device.id)}>
        {selected === device.id && <circle r=".72" fill="#79d9b21c" stroke="#79d9b2" strokeWidth=".06" />}
        <circle r=".36" fill={device.role === 'controller' || device.role === 'access-point' ? '#f3b26f' : '#79d9b2'} stroke="#142221" strokeWidth=".09" />
        <text x=".6" y="-.45" fontSize=".5" fill="#e5eae1" paintOrder="stroke" stroke="#142221" strokeWidth=".15" pointerEvents="none">{device.name}</text>
      </g>)}
      {drawingStart && drawingEnd && <g pointerEvents="none">
        <line x1={drawingStart.x} y1={drawingStart.y} x2={drawingEnd.x} y2={drawingEnd.y} stroke="#f3cf88" strokeWidth=".12" strokeDasharray=".25 .15" />
        <circle cx={drawingStart.x} cy={drawingStart.y} r=".16" fill="#f3cf88" />
        <text x={(drawingStart.x + drawingEnd.x) / 2} y={(drawingStart.y + drawingEnd.y) / 2 - .4}
          textAnchor="middle" fill="#f3cf88" fontSize=".55" paintOrder="stroke" stroke="#142221" strokeWidth=".15">{previewLength.toFixed(2)} m</text>
      </g>}
    </svg>
    {tool === 'wall' && <p className="drawing-hint" role="status">{drawingMessage || 'Haz clic en el inicio y el final de la pared. Ajuste: 0,1 m. Escape cancela.'}</p>}
  </>;
}
