import type { CoverageMapJob } from '../generated/coverage-map.ts';
import { validateMapResult } from './coverage.ts';
import type { CoverageRequest } from './coverage.ts';

export type MapState = { state: 'idle' | 'submitting' | CoverageMapJob['state']; progress: number; result: CoverageMapJob['result']; error: string | null };
export type MapTransport = { create: (request: CoverageRequest) => Promise<CoverageMapJob>;
  read: (id: string) => Promise<CoverageMapJob>; cancel: (id: string) => Promise<unknown> };
const idle = (): MapState => ({ state: 'idle', progress: 0, result: null, error: null });

export class CoverageRunner {
  private epoch = 0;
  private jobId: string | null = null;
  private transport: MapTransport;
  private publish: (state: MapState) => void;
  private sleep: () => Promise<void>;
  constructor(transport: MapTransport, publish: (state: MapState) => void,
    sleep = () => new Promise<void>(resolve => setTimeout(resolve, 250))) {
    this.transport = transport; this.publish = publish; this.sleep = sleep;
  }
  invalidate(silent = false) {
    this.epoch += 1;
    const jobId = this.jobId; this.jobId = null;
    if (jobId) void this.transport.cancel(jobId).catch(() => {});
    if (!silent) this.publish(idle());
  }
  async cancel() {
    const jobId = this.jobId; this.jobId = null;
    const epoch = ++this.epoch;
    this.publish({ ...idle(), state: 'cancelled' });
    if (jobId) {
      try { await this.transport.cancel(jobId); }
      catch { if (epoch === this.epoch) this.publish({ ...idle(), state: 'cancelled', error: 'Resultado descartado. No se pudo confirmar la cancelación en la API local.' }); }
    }
  }
  async start(input: CoverageRequest) {
    this.invalidate(true);
    const epoch = this.epoch, request = structuredClone(input);
    this.publish({ ...idle(), state: 'submitting' });
    try {
      let job = await this.transport.create(request);
      if (epoch !== this.epoch) { void this.transport.cancel(job.job_id).catch(() => {}); return; }
      this.jobId = job.job_id;
      const id = job.job_id, hash = job.request_hash;
      for (;;) {
        if (epoch !== this.epoch) return;
        if (!['queued', 'running', 'done', 'cancelled', 'failed'].includes(job.state) || !Number.isFinite(job.progress) || job.progress < 0 || job.progress > 1) {
          throw new Error('El progreso recibido del servidor no es válido. Vuelve a calcular.');
        }
        if (job.job_id !== id || job.request_hash !== hash) throw new Error('La respuesta de progreso no corresponde al trabajo solicitado.');
        if (job.state === 'done') {
          if (!job.result) throw new Error('El trabajo ha terminado sin un mapa.');
          validateMapResult(job.result, request, hash);
          this.jobId = null;
          this.publish({ state: 'done', progress: 1, result: job.result, error: null }); return;
        }
        this.publish({ state: job.state, progress: job.progress, result: null, error: job.error });
        if (job.state === 'failed' || job.state === 'cancelled') { this.jobId = null; return; }
        await this.sleep(); if (epoch !== this.epoch) return;
        job = await this.transport.read(id);
      }
    } catch (e) {
      if (epoch !== this.epoch) return;
      const id = this.jobId; this.jobId = null;
      if (id) void this.transport.cancel(id).catch(() => {});
      this.publish({ ...idle(), state: 'failed', error: e instanceof Error ? e.message : String(e) });
    }
  }
}
