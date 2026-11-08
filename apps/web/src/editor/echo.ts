/**
 * Canonical JSON for checking that a response echoes the request: object keys sorted and keys whose
 * value is null or undefined dropped. The API adds optional contract fields with a null default
 * (B-113 radio provenance, B-114/B-134 scenario, B-119 distance limits); a request that omits them
 * is echoed with null, and must still match. Any real value that differs is still caught.
 */
export function stableEcho(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stableEcho).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    const object = value as Record<string, unknown>;
    return `{${Object.keys(object).filter(key => object[key] !== null && object[key] !== undefined).sort()
      .map(key => `${JSON.stringify(key)}:${stableEcho(object[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}
