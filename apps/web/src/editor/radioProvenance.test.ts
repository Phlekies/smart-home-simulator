import assert from 'node:assert/strict';
import test from 'node:test';
import { genericRadio } from './connections.ts';
import { allowedProvenance, radioEditPatch, withRadioProvenance } from './radioProvenance.ts';
import type { Radio } from '../generated/project.ts';

test('provenance distinguishes a real zero from an absent value and an unknown protocol', () => {
  const radio = { ...genericRadio('fixture'), channel: 0 };
  assert.ok(allowedProvenance(radio, 'channel').includes('measured'));
  assert.ok(!allowedProvenance(radio, 'channel').includes('unknown'));
  assert.deepEqual(allowedProvenance(radio, 'protocol'), ['unknown', 'inferred']);
  assert.throws(() => withRadioProvenance(radio, 'tx_power_dbm', 'measured', 'fixture'), /valor actual/);
  assert.throws(() => withRadioProvenance(radio, 'channel', 'unknown', ''), /valor actual/);
});

test('adding and removing provenance preserve the other parameters and the radio values', () => {
  const radio: Radio = { ...genericRadio('fixture'), tx_power_dbm: 13,
    provenance: { channel: { provenance: 'unknown', source: null } } };
  const updated = withRadioProvenance(radio, 'tx_power_dbm', 'declared', '  Equipo de prueba  ');
  assert.deepEqual(updated, { channel: { provenance: 'unknown', source: null },
    tx_power_dbm: { provenance: 'declared', source: 'Equipo de prueba' } });
  assert.deepEqual(radio.provenance, { channel: { provenance: 'unknown', source: null } });
  assert.equal(radio.tx_power_dbm, 13);
  assert.equal(withRadioProvenance(radio, 'channel', '', 'will be ignored'), null);
  assert.throws(() => withRadioProvenance(radio, 'tx_power_dbm', 'declared', 'x'.repeat(501)), /500/);
});

test('numeric edits discard only outdated sources, even when both values are known', () => {
  const radio: Radio = { ...genericRadio('fixture'), tx_power_dbm: 10,
    provenance: { protocol: { provenance: 'unknown', source: 'Sin ficha' },
      tx_power_dbm: { provenance: 'measured', source: 'Prueba sintética' } } };
  assert.deepEqual(radioEditPatch(radio, { tx_power_dbm: 10 }), { tx_power_dbm: 10 });
  assert.deepEqual(radioEditPatch(radio, { tx_power_dbm: 11 }),
    { tx_power_dbm: 11, provenance: { protocol: { provenance: 'unknown', source: 'Sin ficha' } } });
  assert.deepEqual(radioEditPatch(radio, { protocol: 'wifi', tx_power_dbm: null }),
    { protocol: 'wifi', tx_power_dbm: null, provenance: null });
  assert.deepEqual(radioEditPatch(radio, { bandwidth_hz: 40e6 }), { bandwidth_hz: 40e6 });
  assert.deepEqual(radioEditPatch(radio, { provenance: null }), { provenance: null });
  assert.equal(radio.provenance?.tx_power_dbm?.source, 'Prueba sintética');
});
