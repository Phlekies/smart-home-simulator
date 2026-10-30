import assert from 'node:assert/strict';
import test from 'node:test';
import { bindReference, defaultReferenceView, imageDigest, makeReference, matchesReference, sameSimulationProject } from './referencePersistence.ts';
import type { LocalReferenceImage } from './referencePersistence.ts';
import { adoptHistory, editHistory, emptyHistory, redoHistory, undoHistory } from './history.ts';
import { coverageFixture } from './coverageFixture.ts';
import { RecoveryStore } from './recovery.ts';
import type { Project } from '../generated/project.ts';

function fixture() {
  const image: LocalReferenceImage = { url: 'blob:session-only', fileName: 'test-plan.png', mediaType: 'image/png',
    sha256: 'a'.repeat(64), widthPx: 800, heightPx: 600 };
  const a = { x: 100.125, y: 300.25 }, b = { x: 700.375, y: 300.25 };
  return { image, a, b, saved: makeReference(image, a, b, 12.005, { originX: -2.125, originY: 3.75 }) };
}

test('SHA-256 uses the file bytes, with a standard known vector and distinct-content rejection', async () => {
  const bytes = (value: string) => new TextEncoder().encode(value).buffer;
  assert.equal(await imageDigest(bytes('abc')), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
  assert.notEqual(await imageDigest(bytes('abc')), await imageDigest(bytes('abd')));
});
test('canonical metadata preserves fractional calibration and excludes local resources and view settings', () => {
  const { saved, image, a } = fixture();
  assert.equal(saved.meters_per_pixel, .02); assert.equal(saved.origin_x_m, -2.125);
  assert.deepEqual(saved.calibration?.point_a_px, a);
  a.x = 0; image.widthPx = 1;
  assert.equal(saved.width_px, 800); assert.equal(saved.calibration?.point_a_px.x, 100.125);
  assert.ok(!JSON.stringify(saved).includes('blob:'));
  assert.deepEqual(Object.keys(saved).sort(), ['file_name', 'media_type', 'sha256', 'width_px', 'height_px',
    'meters_per_pixel', 'origin_x_m', 'origin_y_m', 'calibration', 'evidence'].sort());
});
test('renaming an identical image is allowed; matching a name alone cannot associate another image', () => {
  const { saved, image } = fixture();
  assert.equal(matchesReference(saved, { ...image, fileName: 'renamed.png' }), true);
  for (const changed of [{ ...image, sha256: 'b'.repeat(64) }, { ...image, widthPx: 801 },
    { ...image, heightPx: 601 }, { ...image, mediaType: 'image/jpeg' as const }]) {
    assert.equal(matchesReference(saved, changed), false);
    assert.equal(bindReference(saved, changed, defaultReferenceView()), null);
  }
  assert.equal(bindReference(saved, null, defaultReferenceView()), null);
  assert.equal(bindReference(undefined, image, defaultReferenceView()), null);
});
test('binding recovers the saved scale/origin, while view changes remain transient', () => {
  const { saved, image } = fixture();
  const bound = bindReference(saved, image, { opacity: .3, visible: false });
  assert.deepEqual(bound?.placement, { metersPerPixel: .02, originX: -2.125, originY: 3.75 });
  assert.equal(bound?.opacity, .3); assert.equal(bound?.visible, false);
  assert.equal(bindReference(saved, image, defaultReferenceView())?.opacity, .55);
});
test('metadata without recorded calibration still restores its authoritative placement', () => {
  const { saved, image } = fixture(); saved.calibration = null;
  assert.equal(bindReference(saved, image, defaultReferenceView())?.placement.metersPerPixel, .02);
});
test('project JSON and recovery preserve metadata and original input without persisting image bytes', () => {
  const { saved } = fixture(); const project = coverageFixture().request.project;
  project.plan_reference = saved; project.legacy_source = { original: 'retained' };
  const reopened = JSON.parse(JSON.stringify(project)) as Project;
  assert.deepEqual(reopened.plan_reference, saved); assert.deepEqual(reopened.legacy_source, project.legacy_source);
  let raw: string | null = null;
  const store = new RecoveryStore(() => ({ getItem: () => raw, setItem: (_key, value) => { raw = value; }, removeItem: () => { raw = null; } }));
  store.inspect(); store.save(reopened); const inspected = store.inspect();
  assert.equal(inspected.kind, 'available');
  if (inspected.kind === 'available') assert.deepEqual((inspected.project as Project).plan_reference, saved);
  assert.ok(!raw!.includes('blob:'));
});
test('undo/redo covers reference replacement and removal independently of the local image', () => {
  const { saved } = fixture(); const project = coverageFixture().request.project;
  const initial = adoptHistory(emptyHistory<Project>(), project);
  const added = editHistory(initial, draft => { draft.plan_reference = structuredClone(saved); });
  const replaced = editHistory(added, draft => { draft.plan_reference!.sha256 = 'b'.repeat(64); });
  const removed = editHistory(replaced, draft => { draft.plan_reference = null; });
  assert.equal(undoHistory(removed).present?.plan_reference?.sha256, 'b'.repeat(64));
  assert.equal(undoHistory(undoHistory(removed)).present?.plan_reference?.sha256, saved.sha256);
  assert.equal(redoHistory(undoHistory(removed)).present?.plan_reference, null);
  assert.equal(initial.present?.plan_reference, undefined);
});
test('only reference metadata is ignored for result validity; physical edits remain relevant', () => {
  const { saved } = fixture(); const project = coverageFixture().request.project;
  const withReference = { ...project, plan_reference: saved };
  assert.equal(sameSimulationProject(project, withReference), true);
  assert.equal(sameSimulationProject(withReference, { ...withReference, plan_reference: null }), true);
  const moved = structuredClone(withReference); moved.devices[0].position.x += .125;
  assert.equal(sameSimulationProject(withReference, moved), false);
  assert.equal(sameSimulationProject(withReference, { ...withReference, settings: { ...withReference.settings, system_gain_db: 1 } }), false);
  assert.equal(sameSimulationProject(project, null), false);
});
test('invalid identity or physical calibration cannot enter saved metadata', () => {
  const { image, a, b } = fixture();
  for (const changed of [{ ...image, sha256: 'INVALID' }, { ...image, fileName: '' }, { ...image, fileName: 'a'.repeat(256) }]) {
    assert.throws(() => makeReference(changed, a, b, 12, { originX: 0, originY: 0 }));
  }
  assert.throws(() => makeReference(image, a, b, 12, { originX: 10000, originY: 0 }));
  assert.throws(() => makeReference(image, a, a, 12, { originX: 0, originY: 0 }));
});
