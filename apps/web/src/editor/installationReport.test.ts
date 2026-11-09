import assert from 'node:assert/strict';
import test from 'node:test';
import type { InstallationReport } from '../generated/installation-report.ts';
import { coverageFixture } from './coverageFixture.ts';
import { requestInstallationReport, validateInstallationReport } from './installationReport.ts';

function fixture() {
  const { request: { project }, result: map } = coverageFixture();
  const report: InstallationReport = { title: 'Installation', project_name: project.name, engine: map.engine,
    engine_version: map.engine_version, input_hash: map.input_hash, links: [], counts: {}, scope: 'Test',
    pending_decisions: [], not_evaluated: [], limitations: [] };
  const mapEntry = { title: 'Test map', result: structuredClone(map), summary: {
    cells: 2, computed_cells: 0, partial_cells: 1, not_computed_cells: 1, limiting_margin_db: null, negative_limiting_cells: 0 } };
  return { project, report, map, mapEntry };
}

test('accepts a map-only report with the same request and preserves missing values', () => {
  const { project, report, map, mapEntry } = fixture();
  report.maps = [mapEntry];
  validateInstallationReport(report, project, map);
  assert.deepEqual(report.maps[0].result.cells.forward_margin_db, [null, null]);
});

test('rejects unsolicited maps, missing maps and maps from another request or revision', () => {
  const { project, report, map, mapEntry } = fixture();
  validateInstallationReport(report, project, null);
  assert.throws(() => validateInstallationReport(report, project, map));
  report.maps = [mapEntry];
  assert.throws(() => validateInstallationReport(report, project, null));
  mapEntry.result.request_hash = 'd'.repeat(64);
  assert.throws(() => validateInstallationReport(report, project, map));
  mapEntry.result.request_hash = map.request_hash;
  mapEntry.result.input_hash = 'c'.repeat(64);
  assert.throws(() => validateInstallationReport(report, project, map));
});

test('rejects another project, engine or missing link', () => {
  const { project, report } = fixture();
  assert.throws(() => validateInstallationReport({ ...report, project_name: 'Another' }, project, null));
  assert.throws(() => validateInstallationReport({ ...report, engine: 'sionna-rt' }, project, null));
  project.links.push({ id: 'missing', source_device_id: 'ap', source_radio_id: 'r',
    target_device_id: 'sensor', target_radio_id: 'radio-1' });
  assert.throws(() => validateInstallationReport(report, project, null));
});

test('downloads full JSON with B-135 evidence levels and sends only the selected map parameters', async context => {
  const { project, report, map, mapEntry } = fixture();
  report.maps = [mapEntry];
  report.evidence_levels = [
    { level: 'consistency', status: 'checked', detail: 'Casos analíticos' },
    { level: 'calibration', status: 'none', detail: 'Sin medidas de ajuste' },
    { level: 'validation', status: 'none', detail: 'Sin contraste independiente' },
  ];
  const signal = new AbortController().signal;
  context.mock.method(globalThis, 'fetch', async (path: string, options: RequestInit) => {
    assert.equal(path, '/api/reports');
    assert.deepEqual(JSON.parse(String(options.body)), { project, maps: [map.parameters] });
    assert.equal(options.signal, signal);
    return Response.json(report);
  });
  const downloaded = await requestInstallationReport('json', project, map, signal);
  assert.deepEqual(JSON.parse(downloaded), report);
});

test('downloads Markdown as supplied by B-135 and rejects other response formats', async context => {
  const { project } = fixture();
  const markdown = '## Nivel de evidencia\n\nValidación experimental pendiente.\n';
  const response = context.mock.method(globalThis, 'fetch', async (path: string, options: RequestInit) => {
    assert.equal(path, '/api/reports/markdown');
    assert.deepEqual(JSON.parse(String(options.body)), { project });
    return new Response(markdown, { headers: { 'Content-Type': 'text/markdown; charset=utf-8' } });
  });
  assert.equal(await requestInstallationReport('markdown', project, null), markdown);
  response.mock.mockImplementation(async () => Response.json({ unexpected: true }));
  await assert.rejects(() => requestInstallationReport('markdown', project, null), /formato/);
});
