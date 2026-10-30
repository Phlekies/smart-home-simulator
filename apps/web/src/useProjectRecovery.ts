import { useEffect, useState } from 'react';
import { api } from './api';
import { RecoverySaver, RecoveryStore } from './editor/recovery';
import type { Project } from './generated/project';

export function useProjectRecovery(project: Project | null) {
  const [session] = useState(() => {
    const store = new RecoveryStore(() => window.localStorage);
    return { store, inspection: store.inspect(), saver: new RecoverySaver(store, async p => {
      try { return await api<Project>('/projects/import', p); }
      catch { throw new Error('Comprueba los datos del proyecto y que la API local esté activa.'); }
    }) };
  });
  const [pending, setPending] = useState(session.inspection.kind === 'available' || session.inspection.kind === 'invalid');
  const [saved, setSaved] = useState<{ project: Project; at: string } | null>(null);
  const [error, setError] = useState(session.inspection.kind === 'unavailable' ? session.inspection.message : '');
  const [retry, setRetry] = useState(0);
  const unsaved = !pending && project !== null && saved?.project !== project;

  useEffect(() => {
    if (pending || !project) return;
    let active = true;
    const timer = window.setTimeout(() => {
      void session.saver.save(project).then(at => {
        if (active && at) { setSaved({ project, at }); setError(''); }
      }).catch(e => {
        if (active) setError(`No se pudo actualizar la recuperación. La última copia disponible se conserva. ${String(e)}`);
      });
    }, 500);
    return () => { active = false; window.clearTimeout(timer); session.saver.cancel(); };
  }, [project, pending, retry, session]);

  useEffect(() => {
    if (!unsaved) return;
    const beforeUnload = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ''; };
    window.addEventListener('beforeunload', beforeUnload);
    return () => window.removeEventListener('beforeunload', beforeUnload);
  }, [unsaved]);

  function discard() {
    try { session.store.discard(); setPending(false); setError(''); }
    catch (e) { setError(`No se pudo descartar la copia local. ${String(e)}`); }
  }
  function accept(project: Project) {
    if (session.inspection.kind !== 'available') return;
    setSaved({ project, at: session.inspection.savedAt }); setPending(false); setError('');
  }
  return { inspection: session.inspection, pending, savedAt: saved?.at, unsaved, error, discard, accept,
    retry: () => setRetry(value => value + 1) };
}
