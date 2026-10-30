export async function api<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api${path}`, body === undefined ? { signal } : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = typeof payload.detail === 'string' ? payload.detail : JSON.stringify(payload.detail ?? response.status);
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}
