import assert from 'node:assert/strict';
import test from 'node:test';
import {
  adoptHistory, editHistory, emptyHistory, finishGesture, HISTORY_LIMIT,
  redoHistory, startGesture, undoHistory,
} from './history.ts';

type Snapshot = { position: { x: number }; walls: string[] };
const initial: Snapshot = { position: { x: 0 }, walls: ['original'] };
const open = () => adoptHistory(emptyHistory<Snapshot>(), initial);

test('edits and undo/redo preserve detached snapshots and exact order', () => {
  const first = open();
  const second = editHistory(first, draft => { draft.position.x = 3.25; });
  const third = editHistory(second, draft => { draft.walls.push('new wall'); });
  assert.equal(first.present?.position.x, 0);
  assert.deepEqual(second.present?.walls, ['original']);
  const undone = undoHistory(third);
  assert.deepEqual(undone.present, second.present);
  assert.deepEqual(redoHistory(undone).present, third.present);
  const twice = undoHistory(undone);
  assert.deepEqual(twice.present, initial);
  assert.deepEqual(redoHistory(redoHistory(twice)).present, third.present);
});

test('adoption detaches caller data and resets history', () => {
  const edited = editHistory(open(), draft => { draft.position.x = 8; });
  const incoming: Snapshot = { position: { x: 2 }, walls: ['imported'] };
  const adopted = adoptHistory(undoHistory(edited), incoming);
  incoming.walls.push('outside mutation');
  assert.deepEqual(adopted.present?.walls, ['imported']);
  assert.equal(adopted.past.length, 0);
  assert.equal(adopted.future.length, 0);
  assert.equal(adopted.gestureBase, null);
});

test('branching after undo discards redo; no-op edits do not', () => {
  const changed = editHistory(open(), draft => { draft.position.x = 4; });
  const undone = undoHistory(changed);
  assert.equal(editHistory(undone, () => {}), undone);
  assert.equal(redoHistory(undone).present?.position.x, 4);
  const branched = editHistory(undone, draft => { draft.position.x = 7; });
  assert.equal(branched.future.length, 0);
  assert.equal(redoHistory(branched).present?.position.x, 7);
});

test('many pointer updates form one undoable gesture', () => {
  let history = startGesture(open());
  for (let x = 1; x <= 20; x++) history = editHistory(history, draft => { draft.position.x = x / 10; });
  assert.equal(history.past.length, 0);
  history = finishGesture(history);
  assert.equal(history.past.length, 1);
  assert.equal(history.present?.position.x, 2);
  assert.equal(undoHistory(history).present?.position.x, 0);
  assert.equal(redoHistory(undoHistory(history)).present?.position.x, 2);
});

test('click with no movement and gesture returning to origin do not create entries', () => {
  const moved = editHistory(open(), draft => { draft.position.x = 4; });
  const undone = undoHistory(moved);
  const click = finishGesture(startGesture(undone));
  assert.equal(click.past.length, 0);
  assert.equal(click.future.length, 1);
  let gesture = startGesture(click);
  gesture = editHistory(gesture, draft => { draft.position.x = 9; });
  gesture = editHistory(gesture, draft => { draft.position.x = 0; });
  const cancelledMovement = finishGesture(gesture);
  assert.equal(cancelledMovement.past.length, 0);
  assert.equal(cancelledMovement.future.length, 1);
  assert.equal(redoHistory(cancelledMovement).present?.position.x, 4);
});

test('undo during an active gesture completes then reverses that gesture', () => {
  let history = editHistory(open(), draft => { draft.position.x = 3; });
  history = editHistory(startGesture(history), draft => { draft.position.x = 6; });
  const undone = undoHistory(history);
  assert.equal(undone.gestureBase, null);
  assert.equal(undone.present?.position.x, 3);
  assert.equal(redoHistory(undone).present?.position.x, 6);
});

test('redo during an active changed gesture cannot replay an abandoned branch', () => {
  let history = undoHistory(editHistory(open(), draft => { draft.position.x = 5; }));
  history = editHistory(startGesture(history), draft => { draft.position.x = 8; });
  const completed = redoHistory(history);
  assert.equal(completed.present?.position.x, 8);
  assert.equal(completed.future.length, 0);
  assert.equal(completed.past.length, 1);
});

test('history limit keeps the most recent 50 complete snapshots', () => {
  let history = open();
  for (let x = 1; x <= 80; x++) history = editHistory(history, draft => { draft.position.x = x; });
  assert.equal(history.past.length, HISTORY_LIMIT);
  for (let i = 0; i < HISTORY_LIMIT; i++) history = undoHistory(history);
  assert.equal(history.present?.position.x, 30);
  assert.equal(history.past.length, 0);
  assert.equal(history.future.length, HISTORY_LIMIT);
});

test('empty state and exceptions do not mutate history', () => {
  const empty = emptyHistory<Snapshot>();
  assert.equal(editHistory(empty, () => {}), empty);
  assert.equal(undoHistory(empty), empty);
  assert.equal(redoHistory(empty), empty);
  const history = open();
  assert.throws(() => editHistory(history, draft => { draft.position.x = 99; throw new Error('invalid edit'); }));
  assert.equal(history.present?.position.x, 0);
});
