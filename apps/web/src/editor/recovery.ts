import type { Project } from '../generated/project.ts';

export const RECOVERY_KEY = 'smart-environment.project-recovery';
export const MAX_PROJECT_BYTES = 2_000_000;
const MAX_RECORD_BYTES = MAX_PROJECT_BYTES + 1024;
type StorageAccess = () => Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;
type RecoveryRecord = { version: 1; savedAt: string; project: unknown };
export type RecoveryInspection =
  | { kind: 'empty' }
  | { kind: 'unavailable'; message: string }
  | { kind: 'invalid'; raw: string; message: string }
  | { kind: 'available'; raw: string; savedAt: string; project: unknown };

const bytes = (value: string) => new TextEncoder().encode(value).byteLength;
const object = (value: unknown): value is Record<string, unknown> => value !== null && typeof value === 'object' && !Array.isArray(value);

// This checks the envelope only. The existing API validates the canonical project.
export function inspectRecovery(raw: string | null): RecoveryInspection {
  if (raw === null) return { kind: 'empty' };
  const invalid = (message: string): RecoveryInspection => ({ kind: 'invalid', raw, message });
  if (bytes(raw) > MAX_RECORD_BYTES) return invalid('La copia local supera el tamaño admitido.');
  let record: unknown;
  try { record = JSON.parse(raw); } catch { return invalid('La copia local contiene datos dañados.'); }
  if (!object(record)) return invalid('La copia local no tiene un formato reconocido.');
  if (record.version !== 1) return invalid('La versión de la copia local no es compatible con esta aplicación.');
  if (typeof record.savedAt !== 'string' || !Number.isFinite(Date.parse(record.savedAt))) return invalid('La fecha de la copia local no es válida.');
  if (!object(record.project) || record.project.format !== 'smart-environment-simulator' || record.project.version !== 1) {
    return invalid('El formato o la versión del proyecto guardado no es compatible.');
  }
  if (bytes(JSON.stringify(record.project)) > MAX_PROJECT_BYTES) return invalid('El proyecto guardado supera el límite de 2 MB.');
  return { kind: 'available', raw, savedAt: record.savedAt, project: record.project };
}

export class RecoveryStore {
  private expected: string | null = null;
  private inspected = false;
  private storage: StorageAccess;
  constructor(storage: StorageAccess) { this.storage = storage; }

  inspect(): RecoveryInspection {
    try {
      this.expected = this.storage().getItem(RECOVERY_KEY);
      this.inspected = true;
      return inspectRecovery(this.expected);
    } catch { return { kind: 'unavailable', message: 'El navegador no permite acceder a la copia local. Guarda tu trabajo como JSON.' }; }
  }

  private checkedStorage() {
    const storage = this.storage();
    if (!this.inspected) {
      if (storage.getItem(RECOVERY_KEY) !== null) {
        throw new Error('Hay una copia local que no se pudo leer al iniciar. Guarda tu trabajo como JSON y recarga para recuperarla.');
      }
      this.inspected = true;
    }
    if (storage.getItem(RECOVERY_KEY) !== this.expected) {
      throw new Error('La copia local cambió en otra pestaña. Guarda tu proyecto como JSON y recarga para elegir qué copia abrir.');
    }
    return storage;
  }

  save(project: Project, savedAt = new Date().toISOString()) {
    if (bytes(JSON.stringify(project)) > MAX_PROJECT_BYTES) throw new Error('El proyecto supera el límite de recuperación de 2 MB.');
    const record: RecoveryRecord = { version: 1, savedAt, project };
    const raw = JSON.stringify(record);
    try {
      this.checkedStorage().setItem(RECOVERY_KEY, raw);
    } catch (error) {
      if (error instanceof Error && error.name === 'QuotaExceededError') throw new Error('No hay espacio para actualizar la copia local. Guarda tu trabajo como JSON.');
      throw error;
    }
    this.expected = raw;
    return savedAt;
  }

  discard() {
    this.checkedStorage().removeItem(RECOVERY_KEY);
    this.expected = null;
  }
}

// A response for an earlier edit must never replace the latest recovery snapshot.
export class RecoverySaver {
  private revision = 0;
  private store: RecoveryStore;
  private validate: (project: Project) => Promise<Project>;
  constructor(store: RecoveryStore, validate: (project: Project) => Promise<Project>) { this.store = store; this.validate = validate; }
  cancel() { this.revision += 1; }
  async save(project: Project): Promise<string | null> {
    const revision = ++this.revision;
    try {
      const validated = await this.validate(project);
      if (revision !== this.revision) return null;
      return this.store.save(validated);
    } catch (error) {
      if (revision !== this.revision) return null;
      throw error;
    }
  }
}
