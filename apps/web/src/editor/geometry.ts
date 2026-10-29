import type { Wall } from '../generated/project.ts';

// Match the project contract when editing/importing existing segments. The drawing
// tool separately uses 0.1 m as a practical minimum for creating new walls.
const MIN_SEGMENT_LENGTH_M = 1e-6;
const COORDINATE_LIMIT_M = 10_000;

function finite(value: number, name: string): void {
  if (!Number.isFinite(value)) throw new RangeError(`${name} must be finite`);
}

function coordinate(value: number): void {
  finite(value, 'Wall coordinate');
  if (Math.abs(value) > COORDINATE_LIMIT_M) throw new RangeError('Wall coordinates must be within ±10000 m');
}

export function wallLength(wall: Wall): number {
  return Math.hypot(wall.end.x - wall.start.x, wall.end.y - wall.start.y);
}

function validate(wall: Wall): void {
  for (const point of [wall.start, wall.end]) {
    coordinate(point.x); coordinate(point.y); finite(point.z, 'Wall base');
    if (Math.abs(point.z) > 1000) throw new RangeError('Wall base must be within ±1000 m');
  }
  if (wall.start.z !== wall.end.z) throw new RangeError('Wall bases must be horizontal');
  if (wallLength(wall) < MIN_SEGMENT_LENGTH_M) throw new RangeError('Wall endpoints must be at least 0.000001 m apart');
}

/** Set planar centre, length and azimuth while preserving the wall's physical properties. */
export function transformWall(wall: Wall, centerX: number, centerY: number,
                              lengthM: number, angleDeg: number): Wall {
  coordinate(centerX); coordinate(centerY); finite(lengthM, 'Wall length'); finite(angleDeg, 'Wall angle');
  if (lengthM < MIN_SEGMENT_LENGTH_M) throw new RangeError('Wall length must be at least 0.000001 m');
  // Reduce first to avoid loss of trigonometric precision for very large angles.
  const angle = (angleDeg % 360) * Math.PI / 180;
  const halfX = Math.cos(angle) * lengthM / 2;
  const halfY = Math.sin(angle) * lengthM / 2;
  const transformed: Wall = {
    ...wall,
    start: { x: centerX - halfX, y: centerY - halfY, z: wall.start.z },
    end: { x: centerX + halfX, y: centerY + halfY, z: wall.end.z },
  };
  validate(transformed);
  return transformed;
}

/** Translate without rounding the endpoints; this preserves length and orientation. */
export function translateWall(wall: Wall, dx: number, dy: number): Wall {
  finite(dx, 'Wall displacement'); finite(dy, 'Wall displacement');
  const translated: Wall = {
    ...wall,
    start: { ...wall.start, x: wall.start.x + dx, y: wall.start.y + dy },
    end: { ...wall.end, x: wall.end.x + dx, y: wall.end.y + dy },
  };
  validate(translated);
  return translated;
}
