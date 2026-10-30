import type { Point } from '../generated/project.ts';

/** Create an exact horizontal segment; the visual drawing grid does not round these coordinates. */
export function wallPoints(x1: number, y1: number, x2: number, y2: number): [Point, Point] {
  const coordinates = [x1, y1, x2, y2];
  if (!coordinates.every(value => Number.isFinite(value) && Math.abs(value) <= 10_000)) {
    throw new RangeError('Indica coordenadas válidas entre −10000 y 10000 m.');
  }
  // Decimal subtraction at a large origin can lose a few machine precision bits.
  // This tolerance accepts a nominal 0.1 m segment without changing its endpoints.
  const tolerance = Number.EPSILON * Math.max(1, ...coordinates.map(Math.abs)) * 8;
  if (Math.hypot(x2 - x1, y2 - y1) < .1 - tolerance) {
    throw new RangeError('La pared debe medir al menos 0,1 m. Separa sus puntos de inicio y fin.');
  }
  return [{ x: x1, y: y1, z: 0 }, { x: x2, y: y2, z: 0 }];
}
