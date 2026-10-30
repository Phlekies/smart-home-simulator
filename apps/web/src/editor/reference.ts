export type PixelPoint = { x: number; y: number };
export type ReferencePlacement = { metersPerPixel: number; originX: number; originY: number };
export type PlanReference = {
  url: string; name: string; widthPx: number; heightPx: number;
  placement: ReferencePlacement; opacity: number; visible: boolean;
};

export const MAX_IMAGE_BYTES = 8_000_000;
export const MAX_IMAGE_DIMENSION = 16_384;
export const MAX_IMAGE_PIXELS = 16_000_000;
const COORDINATE_LIMIT_M = 10_000;

function validateDimensions(widthPx: number, heightPx: number): void {
  if (![widthPx, heightPx].every(value => Number.isInteger(value) && value > 0 && value <= MAX_IMAGE_DIMENSION)
    || widthPx * heightPx > MAX_IMAGE_PIXELS) {
    throw new RangeError('La imagen debe tener dimensiones enteras positivas, hasta 16384 píxeles por lado y 16 millones de píxeles en total.');
  }
}

/** Calibrate from exact image coordinates; do not snap the reference points to the wall grid. */
export function calibrateReference(a: PixelPoint, b: PixelPoint, distanceM: number,
                                   widthPx: number, heightPx: number): number {
  validateDimensions(widthPx, heightPx);
  for (const point of [a, b]) {
    if (!Number.isFinite(point.x) || !Number.isFinite(point.y)
      || point.x < 0 || point.x > widthPx || point.y < 0 || point.y > heightPx) {
      throw new RangeError('Los puntos de referencia deben estar dentro de la imagen.');
    }
  }
  const pixels = Math.hypot(b.x - a.x, b.y - a.y);
  if (pixels < 2) throw new RangeError('Separa los puntos de referencia al menos 2 píxeles.');
  if (!Number.isFinite(distanceM) || distanceM < .01 || distanceM > 20_000) {
    throw new RangeError('La distancia conocida debe estar entre 0,01 y 20000 m.');
  }
  return distanceM / pixels;
}

/** Axis-aligned image extent, in the same metre coordinates as the plan. */
export function referenceBounds(widthPx: number, heightPx: number, placement: ReferencePlacement): {
  minX: number; minY: number; maxX: number; maxY: number;
} {
  validateDimensions(widthPx, heightPx);
  const { metersPerPixel, originX, originY } = placement;
  if (!Number.isFinite(metersPerPixel) || metersPerPixel <= 0) {
    throw new RangeError('La escala de la imagen debe ser un número positivo.');
  }
  const widthM = widthPx * metersPerPixel;
  const heightM = heightPx * metersPerPixel;
  if (widthM < .01 || heightM < .01) throw new RangeError('La imagen debe ocupar al menos 0,01 m en cada eje.');
  const bounds = { minX: originX, minY: originY, maxX: originX + widthM, maxY: originY + heightM };
  if (!Object.values(bounds).every(value => Number.isFinite(value) && Math.abs(value) <= COORDINATE_LIMIT_M)) {
    throw new RangeError('La imagen completa debe quedar dentro de las coordenadas de −10000 a 10000 m.');
  }
  return bounds;
}

export function imageFileError(type: string, size: number): string | null {
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(type)) return 'Elige una imagen PNG, JPEG o WebP.';
  if (!Number.isInteger(size) || size <= 0) return 'El archivo de imagen está vacío o su tamaño no es válido.';
  if (size > MAX_IMAGE_BYTES) return 'La imagen supera el límite de 8 MB.';
  return null;
}
