import type { InstallationReport } from '../generated/installation-report.ts';
import type { CoverageMapResult } from '../generated/coverage-map.ts';
import type { Project } from '../generated/project.ts';
import { validateMapResult } from './coverage.ts';
import { stable } from './latestAnalysis.ts';

export const installationReportFormats = {
  markdown: { endpoint: '/reports/markdown', type: 'text/markdown', filename: 'informe-instalacion.md' },
  json: { endpoint: '/reports', type: 'application/json', filename: 'informe-instalacion.json' },
} as const;

export async function requestInstallationReport(format: keyof typeof installationReportFormats, project: Project,
  map: CoverageMapResult | null, signal?: AbortSignal): Promise<string> {
  const output = installationReportFormats[format];
  const response = await apiResponse(output.endpoint, { project, ...(map ? { maps: [map.parameters] } : {}) }, signal);
  if (response.headers.get('content-type')?.split(';')[0] !== output.type) {
    throw new Error('La API local devolvió un formato de informe inesperado.');
  }
  if (format === 'json') {
    const report: InstallationReport = await response.json();
    validateInstallationReport(report, project, map);
    return JSON.stringify(report, null, 2);
  }
  const text = await response.text();
  if (!text.trim()) throw new Error('La API local devolvió un informe vacío.');
  return text;
}

export function validateInstallationReport(report: InstallationReport, project: Project, map: CoverageMapResult | null) {
  if (report.project_name !== project.name || report.engine !== 'quick-estimate' || !/^[a-f0-9]{64}$/.test(report.input_hash)
    || stable(report.links.map(link => link.link_id).sort()) !== stable(project.links.map(link => link.id).sort())) {
    throw new Error('El informe recibido pertenece a otro proyecto o no contiene los enlaces solicitados.');
  }
  const maps = report.maps ?? [];
  if (maps.length !== (map ? 1 : 0)) throw new Error('El informe no contiene los mapas solicitados.');
  if (!map) return;
  const returned = maps[0].result;
  if (report.input_hash !== map.input_hash || returned.input_hash !== map.input_hash
    || report.engine_version !== map.engine_version || returned.engine_version !== map.engine_version) {
    throw new Error('El mapa incluido ya no coincide con el informe. Vuelve a calcular el mapa.');
  }
  validateMapResult(returned, { project, ...map.parameters }, map.request_hash);
}
import { apiResponse } from '../api.ts';
