export type AnalysisState<T> = { pending: boolean; result: T | null; error: string | null };
const empty = <T>(): AnalysisState<T> => ({ pending: false, result: null, error: null });
export class LatestAnalysis<T> {
  private epoch = 0;
  private controller: AbortController | null = null;
  private publish: (state: AnalysisState<T>) => void;
  constructor(publish: (state: AnalysisState<T>) => void) { this.publish = publish; }
  invalidate(silent = false) {
    this.epoch += 1; this.controller?.abort(); this.controller = null;
    if (!silent) this.publish(empty<T>());
  }
  async run<R>(input: R, perform: (request: R, signal: AbortSignal) => Promise<T>, validate: (result: T, request: R) => void) {
    this.invalidate(true); const epoch = this.epoch, request = structuredClone(input), controller = new AbortController();
    this.controller = controller; this.publish({ ...empty<T>(), pending: true });
    try {
      const result = await perform(request, controller.signal);
      if (epoch !== this.epoch) return;
      validate(result, request); this.controller = null; this.publish({ pending: false, result, error: null });
    } catch (e) {
      if (epoch !== this.epoch) return;
      this.controller = null; this.publish({ ...empty<T>(), error: e instanceof Error ? e.message : String(e) });
    }
  }
}
export function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    const object = value as Record<string, unknown>;
    return `{${Object.keys(object).sort().map(key => `${JSON.stringify(key)}:${stable(object[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}
