import test from 'node:test';
import assert from 'node:assert/strict';
import type { GenericProfile } from '../generated/radio-profile.ts';
import { genericRadio } from './connections.ts';
import { profileReceiver } from './radioProfiles.ts';
const profile = (): GenericProfile => ({ id: 'synthetic', name: 'Test', description: 'Test only', protocol: 'wifi', band: '2.4GHz', mode: 'Synthetic mode', bandwidth_hz: 20e6,
  sensitivity_dbm: { value: -82, provenance: 'standard-minimum', source: 'Synthetic reference, not a verified product' }, tx_power_dbm: { value: null, provenance: 'unknown', source: null },
  antenna_gain_dbi: { value: 0, provenance: 'inferred', source: 'Test assumption' }, noise_figure_db: { value: 7, provenance: 'inferred', source: 'Test assumption' }, notes: ['Unverified test only'] });
test('generic clients follow AP frequency/channel without copying AP power or antenna pattern', () => {
  const ap = { ...genericRadio('ap'), channel: 11, tx_power_dbm: 30, antenna: 'directional' as const };
  const client = profileReceiver(profile(), ap);
  assert.equal(client.radio.frequency_hz, ap.frequency_hz); assert.equal(client.radio.channel, 11);
  assert.equal(client.radio.tx_power_dbm, null); assert.equal(client.radio.tx_gain_dbi, 0); assert.equal(client.radio.antenna, 'omnidirectional');
  assert.match(client.evidence, /Unverified test only/); assert.match(client.evidence, /inferred/);
});
test('zero TX is numeric and a sourced explicit override preserves provenance', () => {
  const original = profile(), ap = genericRadio('ap');
  const client = profileReceiver(original, ap, { value: 0, provenance: 'measured', source: 'Synthetic test instrument' });
  assert.equal(client.radio.tx_power_dbm, 0); assert.match(client.evidence, /measured/); assert.match(client.evidence, /Synthetic test instrument/);
  assert.equal(original.tx_power_dbm.value, null); assert.equal(ap.tx_power_dbm, null);
});
test('out-of-band, other protocols and bandwidth mismatch reject a generic profile', () => {
  for (const ap of [{ ...genericRadio('ap'), frequency_hz: 5e9 }, { ...genericRadio('ap'), protocol: 'zigbee' as const }, { ...genericRadio('ap'), bandwidth_hz: 40e6 }]) {
    assert.throws(() => profileReceiver(profile(), ap));
  }
});
test('missing required inferred values and unsupported overrides never receive defaults', () => {
  const missing = profile(); missing.noise_figure_db = { value: null, provenance: 'unknown', source: null };
  assert.throws(() => profileReceiver(missing, genericRadio('ap')));
  for (const tx of [{ value: -101, provenance: 'declared' as const, source: 'test' }, { value: NaN, provenance: 'measured' as const, source: 'test' },
    { value: 10, provenance: 'inferred' as const, source: 'test' }, { value: 0, provenance: 'declared' as const, source: '  ' }]) assert.throws(() => profileReceiver(profile(), genericRadio('ap'), tx));
});
