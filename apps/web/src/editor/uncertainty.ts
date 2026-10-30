import type { Material, MaterialUncertainty, Wall } from '../generated/project.ts';

export const doorNames = { open: 'Puerta abierta', closed: 'Puerta cerrada', unknown: 'Puerta de estado desconocido' };
export function withDoor(wall: Wall, state: Wall['door']): Wall { return { ...wall, door: state ?? null }; }

export function validatedMaterialPatch(material: Material, patch: Partial<Material>): Partial<Material> {
  const next = { ...material, ...patch }, range = next.uncertainty;
  if (range) {
    for (const [low, nominal, high] of [[range.loss_db_24ghz_low, next.loss_db_24ghz, range.loss_db_24ghz_high],
      [range.loss_db_5ghz_low, next.loss_db_5ghz, range.loss_db_5ghz_high]]) {
      if (![low, nominal, high].every(value => Number.isFinite(value) && value >= 0 && value <= 1000)
        || low > nominal || nominal > high) throw new Error('Cada rango debe cumplir mínimo ≤ pérdida nominal ≤ máximo, entre 0 y 1000 dB.');
    }
    if (!range.source.trim() || range.source.length > 500) throw new Error('Indica el motivo o fuente del rango, hasta 500 caracteres.');
  }
  return structuredClone(patch);
}
export function makeMaterialRange(material: Material, values: string[], source: string): MaterialUncertainty {
  if (values.length !== 4 || values.some(value => !value.trim() || !Number.isFinite(Number(value)))) throw new Error('Completa los cuatro límites con números finitos.');
  const [loss_db_24ghz_low, loss_db_24ghz_high, loss_db_5ghz_low, loss_db_5ghz_high] = values.map(Number);
  const uncertainty = { loss_db_24ghz_low, loss_db_24ghz_high, loss_db_5ghz_low, loss_db_5ghz_high, source: source.trim() };
  validatedMaterialPatch(material, { uncertainty }); return uncertainty;
}
