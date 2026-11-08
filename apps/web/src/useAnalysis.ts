import { useEffect, useRef, useState } from 'react';
import { LatestAnalysis } from './editor/latestAnalysis';
import type { AnalysisState } from './editor/latestAnalysis';

export function useAnalysis<T>(revision: number) {
  const [state, setState] = useState<AnalysisState<T>>({ pending: false, result: null, error: null });
  const [runner] = useState(() => new LatestAnalysis<T>(setState));
  const submitted = useRef<number | null>(null);
  useEffect(() => { submitted.current = null; runner.invalidate(); return () => runner.invalidate(true); }, [revision, runner]);
  return { ...state, result: submitted.current === revision ? state.result : null,
    clear: () => { submitted.current = null; runner.invalidate(); },
    run: <R,>(request: R, perform: (request: R, signal: AbortSignal) => Promise<T>, validate: (result: T, request: R) => void) => {
      submitted.current = revision; void runner.run(request, perform, validate);
    } };
}
