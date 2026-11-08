import type { PlanReference as SavedReference, Project } from '../generated/project.ts';
import { calibrateReference, referenceBounds } from './reference.ts';
import type { PixelPoint, PlanReference, ReferencePlacement } from './reference.ts';

export type LocalReferenceImage = {
  url: string; fileName: string; mediaType: SavedReference['media_type'];
  sha256: string; widthPx: number; heightPx: number;
};
export type ReferenceView = { opacity: number; visible: boolean };
export const defaultReferenceView = (): ReferenceView => ({ opacity: .55, visible: true });

export async function imageDigest(bytes: ArrayBuffer): Promise<string> {
  if (!globalThis.crypto?.subtle) throw new Error('El navegador no permite comprobar la huella de la imagen. Abre la aplicación mediante localhost.');
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
}

export function matchesReference(saved: SavedReference | null | undefined, image: LocalReferenceImage | null): boolean {
  return !!saved && !!image && saved.sha256 === image.sha256 && saved.width_px === image.widthPx
    && saved.height_px === image.heightPx && saved.media_type === image.mediaType;
}

export function makeReference(image: LocalReferenceImage, a: PixelPoint, b: PixelPoint, distanceM: number,
  origin: Pick<ReferencePlacement, 'originX' | 'originY'>): SavedReference {
  if (!/^[0-9a-f]{64}$/.test(image.sha256)) throw new Error('La huella de la imagen no es válida. Vuelve a cargarla.');
  if (!image.fileName.length || image.fileName.length > 255) throw new Error('El nombre del archivo debe tener entre 1 y 255 caracteres.');
  const metersPerPixel = calibrateReference(a, b, distanceM, image.widthPx, image.heightPx);
  referenceBounds(image.widthPx, image.heightPx, { ...origin, metersPerPixel });
  return { file_name: image.fileName, media_type: image.mediaType, sha256: image.sha256,
    width_px: image.widthPx, height_px: image.heightPx, meters_per_pixel: metersPerPixel,
    origin_x_m: origin.originX, origin_y_m: origin.originY,
    calibration: { point_a_px: { ...a }, point_b_px: { ...b }, distance_m: distanceM },
    evidence: 'Calibración indicada por el usuario a partir de una distancia conocida; sin levantamiento topográfico verificado' };
}

export function bindReference(saved: SavedReference | null | undefined, image: LocalReferenceImage | null,
  view: ReferenceView): PlanReference | null {
  if (!saved || !image || !matchesReference(saved, image)) return null;
  return { url: image.url, name: saved.file_name, widthPx: saved.width_px, heightPx: saved.height_px,
    placement: { metersPerPixel: saved.meters_per_pixel, originX: saved.origin_x_m, originY: saved.origin_y_m }, ...view };
}

// Only the background-image metadata is excluded. Any other project edit remains relevant.
export function sameSimulationProject(a: Project | null, b: Project | null): boolean {
  if (a === b) return true;
  if (!a || !b) return false;
  const { plan_reference: _a, ...left } = a, { plan_reference: _b, ...right } = b;
  return JSON.stringify(left) === JSON.stringify(right);
}
