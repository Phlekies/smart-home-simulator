import assert from 'node:assert/strict';
import test from 'node:test';
import { calibrateReference, imageFileError, MAX_IMAGE_BYTES, referenceBounds } from './reference.ts';

function close(actual: number, expected: number) {
  assert.ok(Math.abs(actual - expected) < 1e-10, `${actual} differs from ${expected}`);
}

test('calibration preserves fractional point coordinates rather than snapping to the wall grid', () => {
  const a = { x: 12.125, y: 8.625 }; const b = { x: 112.625, y: 8.625 };
  close(calibrateReference(a, b, 5.025, 500, 300), .05);
  assert.deepEqual(a, { x: 12.125, y: 8.625 }); assert.deepEqual(b, { x: 112.625, y: 8.625 });
});

test('diagonal, vertical and reversed reference lines use Euclidean distance', () => {
  const a = { x: 10, y: 20 }; const b = { x: 310, y: 420 };
  close(calibrateReference(a, b, 10, 600, 600), .02);
  close(calibrateReference(b, a, 10, 600, 600), .02);
  close(calibrateReference(a, { x: 10, y: 420 }, 8, 600, 600), .02);
});

test('image edges and exact minimum point spacing are accepted', () => {
  close(calibrateReference({ x: 0, y: 0 }, { x: 2, y: 0 }, .01, 400, 200), .005);
  close(calibrateReference({ x: 0, y: 200 }, { x: 400, y: 200 }, 20_000, 400, 200), 50);
});

test('out-of-image, non-finite and indistinguishable reference points are rejected', () => {
  for (const point of [{ x: -0.001, y: 0 }, { x: 401, y: 0 }, { x: 0, y: 201 },
    { x: 0, y: -.001 }, { x: NaN, y: 0 }, { x: 0, y: Infinity }]) {
    assert.throws(() => calibrateReference(point, { x: 2, y: 2 }, 1, 400, 200), RangeError);
    assert.throws(() => calibrateReference({ x: 2, y: 2 }, point, 1, 400, 200), RangeError);
  }
  for (const point of [{ x: 0, y: 0 }, { x: 1.999, y: 0 }, { x: 1, y: 1 }]) {
    assert.throws(() => calibrateReference({ x: 0, y: 0 }, point, 1, 400, 200), /2 píxeles/);
  }
});

test('known distance requires finite values inside the supported range', () => {
  for (const distance of [0, -.1, .0099, 20_000.001, NaN, Infinity, -Infinity]) {
    assert.throws(() => calibrateReference({ x: 0, y: 0 }, { x: 100, y: 0 }, distance, 400, 200), RangeError);
  }
});

test('translated image bounds preserve aspect ratio, exact scale and input placement', () => {
  const placement = { metersPerPixel: .0125, originX: -2.125, originY: 3.75 };
  const bounds = referenceBounds(1200, 800, placement);
  assert.deepEqual(bounds, { minX: -2.125, minY: 3.75, maxX: 12.875, maxY: 13.75 });
  close((bounds.maxX - bounds.minX) / (bounds.maxY - bounds.minY), 1.5);
  assert.deepEqual(placement, { metersPerPixel: .0125, originX: -2.125, originY: 3.75 });
});

test('both dimension and total decoded-pixel limits are checked before use', () => {
  const placement = { metersPerPixel: .01, originX: 0, originY: 0 };
  for (const [width, height] of [[0, 10], [-1, 10], [1.5, 10], [10, NaN], [Infinity, 10],
    [16_385, 1], [1, 16_385], [4001, 4000]]) {
    assert.throws(() => referenceBounds(width, height, placement), RangeError);
    assert.throws(() => calibrateReference({ x: 0, y: 0 }, { x: 2, y: 0 }, 1, width, height), RangeError);
  }
  assert.deepEqual(referenceBounds(4000, 4000, placement), { minX: 0, minY: 0, maxX: 40, maxY: 40 });
  close(referenceBounds(16_384, 1, placement).maxX, 163.84);
});

test('invalid scales and physical dimensions smaller than a centimetre are rejected', () => {
  for (const metersPerPixel of [0, -.1, NaN, Infinity, -Infinity, Number.MIN_VALUE]) {
    assert.throws(() => referenceBounds(100, 100, { metersPerPixel, originX: 0, originY: 0 }), RangeError);
  }
  assert.throws(() => referenceBounds(100, 1, { metersPerPixel: .0099, originX: 0, originY: 0 }), /0,01 m/);
  assert.throws(() => referenceBounds(1, 100, { metersPerPixel: .0099, originX: 0, originY: 0 }), /0,01 m/);
  assert.deepEqual(referenceBounds(1, 1, { metersPerPixel: .01, originX: 0, originY: 0 }),
    { minX: 0, minY: 0, maxX: .01, maxY: .01 });
});

test('the entire image must remain within supported world coordinates', () => {
  const valid = { metersPerPixel: 1, originX: -10_000, originY: 9999 };
  assert.deepEqual(referenceBounds(1, 1, valid), { minX: -10_000, minY: 9999, maxX: -9999, maxY: 10_000 });
  for (const placement of [
    { ...valid, originX: -10_000.01 }, { ...valid, originY: 9999.01 },
    { ...valid, originX: 10_000 }, { ...valid, originY: NaN }, { ...valid, originX: Infinity },
    { ...valid, metersPerPixel: Number.MAX_VALUE },
  ]) assert.throws(() => referenceBounds(2, 1, placement), RangeError);
});

test('supported raster MIME types and the exact byte limit are accepted', () => {
  for (const type of ['image/png', 'image/jpeg', 'image/webp']) {
    assert.equal(imageFileError(type, 1), null); assert.equal(imageFileError(type, MAX_IMAGE_BYTES), null);
  }
});

test('unsupported content types, empty files and invalid/oversized byte counts are rejected', () => {
  for (const type of ['', 'image/svg+xml', 'image/gif', 'image/jpg', 'application/pdf', 'text/plain']) {
    assert.ok(imageFileError(type, 100));
  }
  for (const size of [0, -1, 1.5, NaN, Infinity, MAX_IMAGE_BYTES + 1]) {
    assert.ok(imageFileError('image/png', size));
  }
});
