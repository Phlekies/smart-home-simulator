import type { Radio, RadioValueSource } from '../generated/project.ts';

export const radioParameters = {
  protocol: { label: 'Protocolo', unit: '' },
  channel: { label: 'Canal', unit: '' },
  tx_power_dbm: { label: 'Potencia TX', unit: 'dBm' },
  sensitivity_dbm: { label: 'Sensibilidad', unit: 'dBm' },
  tx_gain_dbi: { label: 'Ganancia TX', unit: 'dBi' },
  rx_gain_dbi: { label: 'Ganancia RX', unit: 'dBi' },
  noise_figure_db: { label: 'Figura de ruido', unit: 'dB' },
} as const;
export type RadioParameter = keyof typeof radioParameters;
export const radioParameterNames = Object.keys(radioParameters) as RadioParameter[];

export function missingRadioValue(radio: Radio, parameter: RadioParameter): boolean {
  return radio[parameter] === null || (parameter === 'protocol' && radio.protocol === 'unknown');
}

export function allowedProvenance(radio: Radio, parameter: RadioParameter): RadioValueSource['provenance'][] {
  // The canonical contract accepts inferred without a value, e.g. legacy assumptions.
  return missingRadioValue(radio, parameter) ? ['unknown', 'inferred'] : ['declared', 'measured', 'standard-minimum', 'inferred'];
}

export function withRadioProvenance(radio: Radio, parameter: RadioParameter,
  provenance: RadioValueSource['provenance'] | '', source: string): NonNullable<Radio['provenance']> | null {
  const values = { ...radio.provenance };
  if (!provenance) {
    delete values[parameter];
  } else {
    if (!allowedProvenance(radio, parameter).includes(provenance)) {
      throw new Error('La procedencia no corresponde al valor actual del parámetro.');
    }
    const trimmed = source.trim();
    if (trimmed.length > 500) throw new Error('La fuente admite hasta 500 caracteres.');
    values[parameter] = { provenance, source: trimmed || null };
  }
  return Object.keys(values).length ? values : null;
}

export function radioEditPatch(radio: Radio, patch: Partial<Radio>): Partial<Radio> {
  if ('provenance' in patch || !radio.provenance) return patch;
  const values = { ...radio.provenance };
  for (const parameter of radioParameterNames) {
    if (parameter in patch && patch[parameter] !== radio[parameter]) delete values[parameter];
  }
  if (Object.keys(values).length === Object.keys(radio.provenance).length) return patch;
  return { ...patch, provenance: Object.keys(values).length ? values : null };
}
