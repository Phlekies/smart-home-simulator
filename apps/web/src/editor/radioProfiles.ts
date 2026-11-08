import type { GenericProfile, ProfileValue } from '../generated/radio-profile.ts';
import type { Radio } from '../generated/project.ts';
import type { ReceiverProfile } from '../generated/coverage-map.ts';
import { genericRadio } from './connections.ts';

export const provenanceNames: Record<ProfileValue['provenance'], string> = { 'standard-minimum': 'Mínimo de referencia del estándar',
  declared: 'Declarado', measured: 'Medido', inferred: 'Inferido', unknown: 'Desconocido' };
export function profileReceiver(profile: GenericProfile, ap: Radio, override: ProfileValue | null = null): ReceiverProfile {
  if (ap.frequency_hz < 2.4e9 || ap.frequency_hz > 2.5e9 || Math.abs(ap.bandwidth_hz - profile.bandwidth_hz) > 1
    || !['wifi', 'unknown'].includes(ap.protocol)) throw new Error('Este perfil requiere un AP Wi-Fi de 2,4 GHz con el mismo ancho de banda. Revisa su radio.');
  const gain = profile.antenna_gain_dbi.value, noise = profile.noise_figure_db.value;
  if (gain === null || noise === null) throw new Error('Faltan ganancia o figura de ruido del perfil; no se completan automáticamente.');
  const tx = override ?? profile.tx_power_dbm;
  if (tx.value !== null && (!Number.isFinite(tx.value) || tx.value < -100 || tx.value > 100 || !['declared', 'measured'].includes(tx.provenance) || !tx.source?.trim() || tx.source.length > 500)) {
    throw new Error('Indica potencia TX entre −100 y 100 dBm, procedencia declarada/medida y su fuente.');
  }
  const values = { sensibilidad: profile.sensitivity_dbm, potencia_TX: tx, ganancia: profile.antenna_gain_dbi, figura_de_ruido: profile.noise_figure_db };
  return { id: profile.id, name: profile.name, radio: { ...genericRadio(`profile-${profile.id}`), protocol: 'wifi',
    frequency_hz: ap.frequency_hz, bandwidth_hz: profile.bandwidth_hz, channel: ap.channel,
    tx_power_dbm: tx.value, tx_gain_dbi: gain, rx_gain_dbi: gain, sensitivity_dbm: profile.sensitivity_dbm.value, noise_figure_db: noise },
    evidence: `Perfil genérico, no producto comercial. ${profile.mode}. ` + Object.entries(values).map(([name, value]) =>
      `${name}: ${value.value ?? 'desconocido'} (${value.provenance}); ${value.source ?? 'sin fuente'}`).join(' | ') + ' | ' + profile.notes.join(' | ') };
}
