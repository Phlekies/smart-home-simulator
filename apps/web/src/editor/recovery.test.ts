import assert from 'node:assert/strict';
import test from 'node:test';
import type { Project } from '../generated/project.ts';
import { inspectRecovery, MAX_PROJECT_BYTES, RECOVERY_KEY, RecoverySaver, RecoveryStore } from './recovery.ts';

const project: Project = {
  format: 'smart-environment-simulator', version: 1, units: 'm', name: 'Casa de prueba',
  building: { width_m: 12, depth_m: 10, walls: [], materials: [{ id: 'test', name: 'Hipótesis',
    loss_db_24ghz: 3, loss_db_5ghz: 5, extra_loss_db_per_cm: 0, evidence: 'Sin calibrar' }] },
  devices: [], links: [], settings: { path_loss_exponent: 2, extra_loss_db_per_m: 0, system_gain_db: 0 },
  migration_notes: ['Altura inferida'], legacy_source: { original: { preserved: true } },
};
const at = '2026-10-30T10:00:00.000Z';
const record = (p: unknown = project) => JSON.stringify({ version: 1, savedAt: at, project: p });
function storage(initial: string | null = null) {
  const values = new Map<string, string>(initial === null ? [] : [[RECOVERY_KEY, initial]]);
  return { getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => { values.set(key, value); },
    removeItem: (key: string) => { values.delete(key); } };
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

test('a saved project round-trips including original Java and notes without history or results', () => {
  const memory = storage(); const store = new RecoveryStore(() => memory);
  assert.equal(store.inspect().kind, 'empty'); store.save(project, at);
  const opened = new RecoveryStore(() => memory).inspect();
  assert.equal(opened.kind, 'available');
  if (opened.kind !== 'available') throw new Error('Expected recovery');
  assert.deepEqual(opened.project, project); assert.equal(opened.savedAt, at);
  assert.deepEqual(Object.keys(JSON.parse(opened.raw)).sort(), ['project', 'savedAt', 'version']);
});

test('corrupt and incompatible snapshots stay available for raw download, never auto-open', () => {
  for (const raw of ['{broken', 'null', '[]', JSON.stringify({ version: 7 }),
    record({ ...project, version: 9 }), record({ ...project, format: 'other' }),
    JSON.stringify({ version: 1, project, savedAt: 'invalid' })]) {
    const opened = inspectRecovery(raw); assert.equal(opened.kind, 'invalid');
    if (opened.kind === 'invalid') assert.equal(opened.raw, raw);
  }
});

test('size limit counts UTF-8 bytes and leaves the previous valid snapshot untouched', () => {
  const memory = storage(record()); const store = new RecoveryStore(() => memory); store.inspect();
  const huge = { ...project, name: 'ñ'.repeat(MAX_PROJECT_BYTES / 2) };
  assert.throws(() => store.save(huge), /2 MB/); assert.equal(memory.getItem(RECOVERY_KEY), record());
  assert.equal(inspectRecovery(record(huge)).kind, 'invalid');
});

test('blocked storage access is reported without crashing startup', () => {
  const store = new RecoveryStore(() => { throw new Error('SecurityError'); });
  assert.equal(store.inspect().kind, 'unavailable');
  assert.throws(() => store.save(project)); assert.throws(() => store.discard());
});

test('retry after blocked storage succeeds only if it cannot overwrite an unread startup copy', () => {
  const memory = storage(); let blocked = true;
  const store = new RecoveryStore(() => { if (blocked) throw new Error('SecurityError'); return memory; });
  assert.equal(store.inspect().kind, 'unavailable'); blocked = false;
  memory.setItem(RECOVERY_KEY, record({ ...project, name: 'No leída' }));
  assert.throws(() => store.save(project), /no se pudo leer/);
  assert.equal(JSON.parse(memory.getItem(RECOVERY_KEY)!).project.name, 'No leída');
  memory.removeItem(RECOVERY_KEY); store.save(project, at);
  assert.equal(memory.getItem(RECOVERY_KEY), record());
});

test('quota failure preserves the earlier copy and permits a later retry', () => {
  const memory = storage(record()); let full = true;
  const store = new RecoveryStore(() => ({ ...memory, setItem: (key, value) => {
    if (full) { const e = new Error('Full'); e.name = 'QuotaExceededError'; throw e; }
    memory.setItem(key, value);
  } }));
  store.inspect(); assert.throws(() => store.save({ ...project, name: 'Actualizado' }), /espacio/);
  assert.equal(memory.getItem(RECOVERY_KEY), record());
  full = false; store.save({ ...project, name: 'Actualizado' }, at);
  assert.equal(JSON.parse(memory.getItem(RECOVERY_KEY)!).project.name, 'Actualizado');
});

test('discard deletes only this recovery key and then permits a fresh project', () => {
  const memory = storage(record()); memory.setItem('unrelated', 'keep');
  const store = new RecoveryStore(() => memory); store.inspect(); store.discard();
  assert.equal(memory.getItem(RECOVERY_KEY), null); assert.equal(memory.getItem('unrelated'), 'keep');
  store.save(project, at); assert.equal(memory.getItem(RECOVERY_KEY), record());
});

test('a change from another tab prevents both overwrite and discard', () => {
  const memory = storage(record()); const store = new RecoveryStore(() => memory); store.inspect();
  const other = record({ ...project, name: 'Otra pestaña' }); memory.setItem(RECOVERY_KEY, other);
  assert.throws(() => store.save(project), /otra pestaña/);
  assert.throws(() => store.discard(), /otra pestaña/); assert.equal(memory.getItem(RECOVERY_KEY), other);
});

test('failed validation cannot overwrite the previous valid project', async () => {
  const memory = storage(record()); const store = new RecoveryStore(() => memory); store.inspect();
  const saver = new RecoverySaver(store, async () => { throw new Error('Name is empty'); });
  await assert.rejects(saver.save({ ...project, name: '' }), /Name/);
  assert.equal(memory.getItem(RECOVERY_KEY), record());
});

test('out-of-order validation responses save only the latest edit', async () => {
  const memory = storage(); const store = new RecoveryStore(() => memory); store.inspect();
  const older = deferred<Project>(); const newer = deferred<Project>(); let calls = 0;
  const saver = new RecoverySaver(store, () => ++calls === 1 ? older.promise : newer.promise);
  const first = saver.save(project); const second = saver.save({ ...project, name: 'Último' });
  newer.resolve({ ...project, name: 'Último' }); assert.ok(await second);
  older.resolve(project); assert.equal(await first, null);
  assert.equal(JSON.parse(memory.getItem(RECOVERY_KEY)!).project.name, 'Último');
});

test('editing again or unmounting cancels in-flight writes, including stale failures', async () => {
  const memory = storage(record()); const store = new RecoveryStore(() => memory); store.inspect();
  const pending = deferred<Project>(); const saver = new RecoverySaver(store, () => pending.promise);
  const task = saver.save(project); saver.cancel(); pending.resolve({ ...project, name: 'Old' });
  assert.equal(await task, null); assert.equal(memory.getItem(RECOVERY_KEY), record());
  const failure = deferred<Project>(); const failing = new RecoverySaver(store, () => failure.promise);
  const failed = failing.save(project); failing.cancel(); failure.reject(new Error('stale'));
  assert.equal(await failed, null);
});

test('the canonical validated project is saved, preserving API normalization', async () => {
  const memory = storage(); const store = new RecoveryStore(() => memory); store.inspect();
  const normalized = { ...project, name: 'Validado' };
  const saver = new RecoverySaver(store, async () => normalized); await saver.save(project);
  assert.deepEqual(JSON.parse(memory.getItem(RECOVERY_KEY)!).project, normalized);
});
