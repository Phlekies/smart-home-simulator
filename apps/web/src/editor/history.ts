/** Immutable history for structured-cloneable, JSON project snapshots. */
export type History<T> = {
  present: T | null;
  past: T[];
  future: T[];
  gestureBase: T | null;
};

export const HISTORY_LIMIT = 50;

export function emptyHistory<T>(): History<T> {
  return { present: null, past: [], future: [], gestureBase: null };
}

export function adoptHistory<T>(_history: History<T>, value: T): History<T> {
  return { present: structuredClone(value), past: [], future: [], gestureBase: null };
}

function sameSnapshot<T>(a: T, b: T): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

function appendPast<T>(past: T[], snapshot: T): T[] {
  return [...past, snapshot].slice(-HISTORY_LIMIT);
}

export function editHistory<T>(history: History<T>, updater: (draft: T) => void): History<T> {
  if (history.present === null) return history;
  const draft = structuredClone(history.present);
  updater(draft);
  if (sameSnapshot(draft, history.present)) return history;
  // A gesture keeps its original undo/redo state until it ends. Returning the
  // pointer to its starting position can therefore remain a genuine no-op.
  if (history.gestureBase !== null) return { ...history, present: draft };
  return { present: draft, past: appendPast(history.past, history.present), future: [], gestureBase: null };
}

export function startGesture<T>(history: History<T>): History<T> {
  if (history.present === null || history.gestureBase !== null) return history;
  return { ...history, gestureBase: structuredClone(history.present) };
}

export function finishGesture<T>(history: History<T>): History<T> {
  if (history.gestureBase === null) return history;
  if (history.present === null || sameSnapshot(history.present, history.gestureBase)) {
    return { ...history, gestureBase: null };
  }
  return {
    present: history.present,
    past: appendPast(history.past, history.gestureBase),
    future: [],
    gestureBase: null,
  };
}

export function undoHistory<T>(history: History<T>): History<T> {
  const completed = finishGesture(history);
  if (completed.present === null || completed.past.length === 0) return completed;
  return {
    present: completed.past[completed.past.length - 1],
    past: completed.past.slice(0, -1),
    future: [completed.present, ...completed.future].slice(0, HISTORY_LIMIT),
    gestureBase: null,
  };
}

export function redoHistory<T>(history: History<T>): History<T> {
  const completed = finishGesture(history);
  if (completed.present === null || completed.future.length === 0) return completed;
  return {
    present: completed.future[0],
    past: appendPast(completed.past, completed.present),
    future: completed.future.slice(1),
    gestureBase: null,
  };
}
