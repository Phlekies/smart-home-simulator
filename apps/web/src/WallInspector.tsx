import type { Project, Wall } from './generated/project';
import { transformWall, wallLength } from './editor/geometry';
import NumberField from './NumberField';

export default function WallInspector({ project, wall, onEdit, onMaterialEdit, onDelete, onGestureStart, onGestureEnd }: {
  project: Project; wall: Wall; onEdit: (next: Wall) => void;
  onMaterialEdit: (id: string, patch: Partial<Project['building']['materials'][number]>) => void;
  onDelete: () => void; onGestureStart: () => void; onGestureEnd: () => void;
}) {
  const length = wallLength(wall);
  const centerX = (wall.start.x + wall.end.x) / 2, centerY = (wall.start.y + wall.end.y) / 2;
  const angle = Math.atan2(wall.end.y - wall.start.y, wall.end.x - wall.start.x) * 180 / Math.PI;
  const material = project.building.materials.find(m => m.id === wall.material_id)!;
  function transform(cx = centerX, cy = centerY, len = length, degrees = angle) {
    try { onEdit(transformWall(wall, cx, cy, len, degrees)); }
    catch { throw new Error('La pared completa debe quedar entre −10000 y 10000 m y conservar extremos distintos.'); }
  }
  function number(label: string, value: number, update: (n: number) => void, min: number, max: number, step = .1) {
    return <NumberField label={label} value={value} min={min} max={max} step={step} onChange={n => { if (n !== null) update(n); }} />;
  }
  return <>
    <span className="eyebrow">PARED SELECCIONADA</span><h2>Geometría y material</h2>
    <p className="helper">Arrastra la pared en el plano o ajusta su posición y orientación. Las dimensiones se expresan en metros.</p>
    <fieldset className="inspector-fields" onFocusCapture={onGestureStart} onBlurCapture={onGestureEnd}>
      <legend className="sr-only">Propiedades de la pared</legend>
      <div className="radio-fields">
        {number('Centro X · m', centerX, n => transform(n), -10000, 10000)}
        {number('Centro Y · m', centerY, n => transform(centerX, n), -10000, 10000)}
        {number('Longitud · m', length, n => transform(centerX, centerY, n), .1, 20000)}
        {number('Ángulo · grados', angle, n => transform(centerX, centerY, length, n), -180, 180, 1)}
        {number('Altura pared · m', wall.height_m, n => onEdit({ ...wall, height_m: n }), .1, 100)}
        {number('Espesor · cm', wall.thickness_m * 100, n => onEdit({ ...wall, thickness_m: n / 100 }), 1, 1000, 1)}
        {number('Cota de base · m', wall.start.z, n => onEdit({ ...wall, start: { ...wall.start, z: n }, end: { ...wall.end, z: n } }), -1000, 1000)}
      </div>
      <label className="field"><span>Material de la pared</span><select value={wall.material_id} onChange={event => onEdit({ ...wall, material_id: event.target.value })}>
        {project.building.materials.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
      </select></label>
      <details className="material-details"><summary>Pérdidas del material · avanzado</summary>
        <p className="helper">Estos valores se comparten con todas las paredes del mismo material. Son hipótesis del modelo, pendientes de calibrar.</p>
        {number('Pérdida base 2.4 GHz · dB', material.loss_db_24ghz, n => onMaterialEdit(material.id, { loss_db_24ghz: n }), 0, 1000)}
        {number('Pérdida base 5 GHz · dB', material.loss_db_5ghz, n => onMaterialEdit(material.id, { loss_db_5ghz: n }), 0, 1000)}
        {number('Pérdida adicional · dB/cm', material.extra_loss_db_per_cm, n => onMaterialEdit(material.id, { extra_loss_db_per_cm: n }), 0, 100, .01)}
        <p className="helper">Procedencia: {material.evidence}</p>
      </details>
    </fieldset>
    <p className="wall-dimensions">Inicio ({wall.start.x.toFixed(2)}, {wall.start.y.toFixed(2)}) · Fin ({wall.end.x.toFixed(2)}, {wall.end.y.toFixed(2)})</p>
    <button className="danger-link" onClick={onDelete}>Eliminar pared</button>
  </>;
}
