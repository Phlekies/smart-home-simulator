import type { LinkResult } from './generated/simulation-result';

export const linkStatusNames: Record<LinkResult['status'], string> = {
  'above-threshold': 'Ambos márgenes de 0 dB o más',
  'below-threshold': 'Margen negativo en algún sentido',
  incompatible: 'Radios incompatibles',
  unverified: 'Sin verificar',
  unsupported: 'Fuera de alcance',
};
