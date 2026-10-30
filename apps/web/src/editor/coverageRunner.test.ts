import assert from 'node:assert/strict';
import test from 'node:test';
import { CoverageRunner } from './coverageRunner.ts';
import type { MapState, MapTransport } from './coverageRunner.ts';
import type { CoverageMapJob } from '../generated/coverage-map.ts';
import { coverageFixture } from './coverageFixture.ts';
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>(yes => { resolve = yes; }); return { promise, resolve };
}
function harness(transport: MapTransport) {
  const states: MapState[] = []; const runner = new CoverageRunner(transport, state => states.push(state), () => Promise.resolve());
  return { states, runner };
}
test('a queued job publishes progress and a verified result', async () => {
  const { request, queued, done } = coverageFixture(); let reads = 0;
  const { states, runner } = harness({ create: async () => queued, read: async () => ++reads === 1 ? { ...queued, state: 'running', progress: .5 } : done, cancel: async () => {} });
  await runner.start(request);
  assert.deepEqual(states.map(state => state.state), ['submitting', 'queued', 'running', 'done']);
  assert.equal(states.at(-1)?.result?.request_hash, queued.request_hash);
});
test('cancelling while POST is pending discards its later response and cancels its server job', async () => {
  const { request, done } = coverageFixture(); const pending = deferred<CoverageMapJob>(); const cancelled: string[] = [];
  const { states, runner } = harness({ create: () => pending.promise, read: async () => done, cancel: async id => { cancelled.push(id); } });
  const running = runner.start(request); await runner.cancel(); pending.resolve(done); await running;
  assert.deepEqual(cancelled, ['job']); assert.equal(states.at(-1)?.state, 'cancelled');
  assert.ok(states.every(state => state.result === null));
});
test('editing the project during polling cannot publish the previous result', async () => {
  const { request, queued, done } = coverageFixture(); const pending = deferred<CoverageMapJob>(), reading = deferred<void>();
  const cancelled: string[] = [];
  const { states, runner } = harness({ create: async () => queued, read: () => { reading.resolve(); return pending.promise; }, cancel: async id => { cancelled.push(id); } });
  const running = runner.start(request); await reading.promise; runner.invalidate(); pending.resolve(done); await running;
  assert.equal(states.at(-1)?.state, 'idle'); assert.ok(states.every(state => state.result === null)); assert.deepEqual(cancelled, ['job']);
});
test('unexpected progress identities and result hashes fail explicitly', async () => {
  for (const mutation of ['job', 'result']) {
    const { request, queued, done } = coverageFixture();
    if (mutation === 'job') done.job_id = 'foreign'; else done.result!.request_hash = 'foreign';
    const { states, runner } = harness({ create: async () => queued, read: async () => done, cancel: async () => {} });
    await runner.start(request); assert.equal(states.at(-1)?.state, 'failed'); assert.equal(states.at(-1)?.result, null);
  }
});
test('HTTP errors and a failed cancellation never turn into a successful map', async () => {
  const { request, queued } = coverageFixture();
  const broken = harness({ create: async () => { throw new Error('501 unavailable'); }, read: async () => queued, cancel: async () => {} });
  await broken.runner.start(request); assert.match(broken.states.at(-1)?.error ?? '', /501/);
  const pending = deferred<CoverageMapJob>(), reading = deferred<void>();
  const running = harness({ create: async () => queued, read: () => { reading.resolve(); return pending.promise; }, cancel: async () => { throw new Error('offline'); } });
  const task = running.runner.start(request); await reading.promise; await running.runner.cancel();
  pending.resolve(queued); await task; assert.equal(running.states.at(-1)?.state, 'cancelled');
  assert.match(running.states.at(-1)?.error ?? '', /confirmar/);
});
test('inputs are detached before transport and unmount cleanup is silent', async () => {
  const { request, done } = coverageFixture(); const pending = deferred<CoverageMapJob>(); let seen = 0;
  const { states, runner } = harness({ create: async input => { seen = input.profile.radio.frequency_hz; return pending.promise; }, read: async () => done, cancel: async () => {} });
  const task = runner.start(request); request.profile.radio.frequency_hz = 5e9;
  runner.invalidate(true); pending.resolve(done); await task;
  assert.equal(seen, 2.412e9); assert.deepEqual(states.map(state => state.state), ['submitting']);
});
test('invalid progress is rejected without polling forever', async () => {
  const { request, queued } = coverageFixture(); queued.progress = NaN;
  const { states, runner } = harness({ create: async () => queued, read: async () => { throw new Error('Should not poll'); }, cancel: async () => {} });
  await runner.start(request); assert.equal(states.at(-1)?.state, 'failed');
  assert.match(states.at(-1)?.error ?? '', /progreso/);
});
