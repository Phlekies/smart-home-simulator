export type Bounds = { minX: number; minY: number; maxX: number; maxY: number };
// Zoom around a world point; scale 1 shows the whole plan, 'fit' resets to it.
export type View = { scale: number; cx: number; cy: number };

export const MIN_SCALE = 1;
export const MAX_SCALE = 20;
const clamp = (n: number, min: number, max: number) => Math.max(min, Math.min(max, n));

export function fitView(base: Bounds): View {
  return { scale: 1, cx: (base.minX + base.maxX) / 2, cy: (base.minY + base.maxY) / 2 };
}

/** Visible world rectangle; the centre stays inside the plan so it can never be lost off-screen. */
export function visibleBounds(base: Bounds, view: View | null): Bounds {
  if (!view || view.scale <= MIN_SCALE) return base;
  const width = (base.maxX - base.minX) / view.scale, height = (base.maxY - base.minY) / view.scale;
  const cx = clamp(view.cx, base.minX + width / 2, base.maxX - width / 2);
  const cy = clamp(view.cy, base.minY + height / 2, base.maxY - height / 2);
  return { minX: cx - width / 2, minY: cy - height / 2, maxX: cx + width / 2, maxY: cy + height / 2 };
}

/** Multiply the zoom by factor, keeping anchor (default: the visible centre) at the same screen position. */
export function zoomView(base: Bounds, view: View | null, factor: number, anchor?: { x: number; y: number }): View | null {
  const current = view ?? fitView(base);
  const scale = clamp(current.scale * factor, MIN_SCALE, MAX_SCALE);
  if (scale <= MIN_SCALE) return null;
  const visible = visibleBounds(base, current);
  const at = anchor ?? { x: (visible.minX + visible.maxX) / 2, y: (visible.minY + visible.maxY) / 2 };
  const ratio = current.scale / scale;
  const cx = at.x - (at.x - (visible.minX + visible.maxX) / 2) * ratio;
  const cy = at.y - (at.y - (visible.minY + visible.maxY) / 2) * ratio;
  const next = visibleBounds(base, { scale, cx, cy });
  return { scale, cx: (next.minX + next.maxX) / 2, cy: (next.minY + next.maxY) / 2 };
}

/** Move the visible area by a world offset; nothing to move while the whole plan is shown. */
export function panView(base: Bounds, view: View | null, dx: number, dy: number): View | null {
  if (!view || view.scale <= MIN_SCALE) return null;
  const next = visibleBounds(base, { ...view, cx: view.cx + dx, cy: view.cy + dy });
  return { scale: view.scale, cx: (next.minX + next.maxX) / 2, cy: (next.minY + next.maxY) / 2 };
}

/** Pixel size of an exported image of the plan: long side 1600 px, never more than 4000 px on either side. */
export function exportSize(base: Bounds, longSide = 1600): { width: number; height: number } {
  const w = base.maxX - base.minX, h = base.maxY - base.minY;
  const scale = Math.min(longSide / Math.max(w, h), 4000 / w, 4000 / h);
  return { width: Math.max(1, Math.round(w * scale)), height: Math.max(1, Math.round(h * scale)) };
}

/** Match SVG's aspect-preserving fit, including any rounding of the raster dimensions. */
export function scaleBar(base: Bounds, plot: { width: number; height: number }) {
  const pixelsPerMetre = Math.min(plot.width / (base.maxX - base.minX), plot.height / (base.maxY - base.minY));
  const limit = 160 / pixelsPerMetre;
  const decade = 10 ** Math.floor(Math.log10(limit));
  const metres = ([5, 2, 1].find(value => value * decade <= limit) ?? 1) * decade;
  return { metres, pixels: metres * pixelsPerMetre };
}
