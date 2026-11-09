export async function apiResponse(path: string, body?: unknown, signal?: AbortSignal): Promise<Response> {
  const response = await fetch(`/api${path}`, body === undefined ? { signal } : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = typeof payload.detail === 'string' ? payload.detail : JSON.stringify(payload.detail ?? response.status);
    throw new Error(detail);
  }
  return response;
}

export async function api<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  return (await apiResponse(path, body, signal)).json() as Promise<T>;
}
