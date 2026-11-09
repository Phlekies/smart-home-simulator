import { useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { installationReportFormats as formats, requestInstallationReport } from './editor/installationReport';
import type { CoverageMapResult } from './generated/coverage-map';
import type { Project } from './generated/project';
import { useAnalysis } from './useAnalysis';

export default function ReportPanel({ project, map, revision, disabled, onValidate, onDownload }: {
  project: Project; map: CoverageMapResult | null; revision: number; disabled: boolean;
  onValidate: () => boolean; onDownload: (data: string, filename: string, type: string) => void;
}) {
  const [format, setFormat] = useState<keyof typeof formats>('markdown');
  const [includeMap, setIncludeMap] = useState(false);
  const prepareButton = useRef<HTMLButtonElement>(null);
  const report = useAnalysis<string>(revision);
  const prepared = report.result;
  const selectedMap = includeMap ? map : null;
  const canPrepare = project.links.length > 0 || selectedMap !== null;
  const output = formats[format];

  function prepare(event: FormEvent) {
    event.preventDefault();
    if (disabled || !canPrepare || report.pending || !onValidate()) return;
    report.run({ project, map: selectedMap }, (request, signal) =>
      requestInstallationReport(format, request.project, request.map, signal));
  }

  return <section className="results-panel panel" aria-labelledby="report-title">
    <span className="eyebrow">GUARDAR PARA LA INSTALACIÓN</span><h2 id="report-title">Informe de instalación</h2>
    <p className="helper">Reúne señal y margen en ambos sentidos, paredes atravesadas, hipótesis y datos pendientes del proyecto actual. El informe se genera en la API local con el estimador de trayecto directo, sin calibración experimental.</p>
    <form onSubmit={prepare}><fieldset className="inspector-fields" disabled={disabled}><legend className="sr-only">Opciones del informe</legend>
      <label className="field"><span>Formato del informe</span><select value={format} onChange={event => {
        setFormat(event.target.value as typeof format); report.clear();
      }}>
        <option value="markdown">Markdown · resumen para leer</option>
        <option value="json">JSON · datos del cálculo</option>
      </select></label>
      <label className="reference-toggle"><input type="checkbox" checked={selectedMap !== null} disabled={!map}
        onChange={event => { setIncludeMap(event.target.checked); report.clear(); }} /> Incluir el mapa vigente</label>
      {map ? <p className="helper">{map.parameters.profile.name} · altura {map.parameters.grid.height_m} m · resolución {map.parameters.grid.resolution_m} m.
        {format === 'markdown' ? ' Incluye el resumen y los puntos exactos.' : ' Incluye los valores de cada celda y los puntos exactos.'}</p>
        : <p className="helper">Calcula un mapa para incluirlo en el informe.</p>}
      <div className="coverage-actions">
        <button ref={prepareButton} type="submit" className="primary" disabled={!canPrepare} aria-disabled={report.pending || undefined}>Preparar informe</button>
        {report.pending && <button type="button" onClick={() => { report.clear(); prepareButton.current?.focus(); }}>Cancelar preparación</button>}
        {prepared !== null && <button type="button" onClick={() => onDownload(prepared, output.filename, output.type)}>Descargar informe {format === 'json' ? 'JSON' : 'Markdown'}</button>}
      </div>
    </fieldset></form>
    <p role="status" className="comparison-state">{report.pending ? 'Preparando el informe en la API local…'
      : prepared !== null ? 'Informe listo para descargar.'
      : canPrepare ? 'El informe se calcula con la instalación y las opciones actuales.' : 'Añade un enlace o incluye un mapa calculado para preparar el informe.'}</p>
    {report.error && <p role="alert" className="message error">No se pudo preparar el informe. {report.error}</p>}
  </section>;
}
