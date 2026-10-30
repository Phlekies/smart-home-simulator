import test from 'node:test';
import assert from 'node:assert/strict';
import { LatestAnalysis } from './latestAnalysis.ts';
import type { AnalysisState } from './latestAnalysis.ts';
function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(yes => { resolve = yes; }); return { resolve, promise }; }
function fixture() { const states: AnalysisState<number>[] = []; return { states, runner: new LatestAnalysis<number>(state => states.push(state)) }; }
test('editing while HTTP is pending aborts its transport and ignores a late successful response', async () => {
  const { states, runner } = fixture(), response = deferred<number>(); let signal: AbortSignal | undefined;
  const task = runner.run({}, async (_request, current) => { signal = current; return response.promise; }, () => {});
  runner.invalidate(); response.resolve(1); await task;
  assert.equal(signal?.aborted, true); assert.equal(states.at(-1)?.result, null); assert.equal(states.at(-1)?.pending, false);
});
test('a later request owns the displayed result even when the old request finishes last', async () => {
  const { states, runner } = fixture(), first = deferred<number>();
  const old = runner.run({}, () => first.promise, () => {});
  await runner.run({}, async () => 2, () => {}); first.resolve(1); await old;
  assert.equal(states.at(-1)?.result, 2);
});
test('transport inputs are detached and validation receives the same original snapshot', async () => {
  const { states, runner } = fixture(), response = deferred<number>(), input = { nested: { value: 1 } };
  let transported = input;
  const task = runner.run(input, async request => { transported = request; return response.promise; }, (_result, request) => { assert.equal(request.nested.value, 1); });
  input.nested.value = 5; response.resolve(1); await task;
  assert.notEqual(transported, input); assert.equal(states.at(-1)?.result, 1);
});
test('HTTP and validation failures cannot retain a previous successful result', async () => {
  for (const validateFailure of [false, true]) {
    const { states, runner } = fixture(); await runner.run({}, async () => 1, () => {});
    await runner.run({}, async () => { if (!validateFailure) throw new Error('HTTP 422'); return 2; }, () => { throw new Error('Foreign result'); });
    assert.equal(states.at(-1)?.result, null); assert.ok(states.at(-1)?.error);
  }
});
test('unmount invalidation is silent and late completion cannot publish', async () => {
  const { states, runner } = fixture(), response = deferred<number>(); const task = runner.run({}, () => response.promise, () => {});
  runner.invalidate(true); response.resolve(1); await task; assert.equal(states.length, 1);
});
