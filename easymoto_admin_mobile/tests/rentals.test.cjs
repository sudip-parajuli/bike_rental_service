const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');

function load(file) {
  const source = fs.readFileSync(path.join(__dirname, '..', file), 'utf8');
  const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2021, esModuleInterop: true } }).outputText;
  const module = { exports: {} };
  new Function('require', 'module', 'exports', compiled)(require, module, module.exports);
  return module.exports;
}
const { rentalDateTime, nepalDate, nepalTime, estimateRentalPrice } = load('lib/rentals.ts');
const { createStaffClient } = load('api/client.ts');
const axios = require('axios');

test('Nepal return time remains 7 PM when the phone/server is in another timezone', () => {
  const iso = rentalDateTime('2026-10-25', '19:00');
  assert.equal(iso, '2026-10-25T13:15:00.000Z');
  assert.equal(nepalTime(iso), '19:00');
});
test('Nepal date crosses midnight ahead of UTC', () => {
  assert.equal(nepalDate('2026-10-25T20:00:00Z'), '2026-10-26');
});
test('Rental estimate includes calendar days, duration discount and agreed extra discount', () => {
  assert.deepEqual(estimateRentalPrice(1000, '2026-10-25', '2026-10-31', 100), { days: 7, autoDiscount: 350, total: 6550 });
  assert.equal(estimateRentalPrice(1500, '2026-10-25', '2026-10-25').total, 1500);
});
test('Invalid estimates cannot be submitted as a confirmed rental', () => {
  assert.equal(estimateRentalPrice(1000, '2026-10-25', '2026-10-24'), null);
  assert.equal(estimateRentalPrice(1000, '2026-10-25', '2026-10-25', 2000), null);
});
test('Impossible dates and out-of-range times are rejected before saving', () => {
  assert.throws(() => rentalDateTime('2026-02-31', '19:00'));
  assert.throws(() => rentalDateTime('2026-10-25', '25:00'));
  assert.throws(() => rentalDateTime('', '19:00'));
  assert.equal(nepalDate(rentalDateTime('2028-02-29', '09:00')), '2028-02-29');
});

function fixture() {
  let access = 'old-access', refresh = 'old-refresh', cleared = 0, expired = 0;
  const store = { access: async () => access, refresh: async () => refresh,
    save: async (a, r) => { access = a; refresh = r; }, clear: async () => { cleared++; access = null; refresh = null; } };
  const client = createStaffClient('https://example.invalid/api/mobile', store, () => expired++);
  client.defaults.adapter = async config => {
    if (config.headers.Authorization === 'Bearer fresh-access') return { status: 200, statusText: 'OK', data: { success: true }, config, headers: {} };
    throw new axios.AxiosError('Unauthorized', 'ERR_BAD_REQUEST', config, null, { status: 401, data: {}, config, headers: {}, statusText: 'Unauthorized' });
  };
  return { client, current: () => ({ access, refresh, cleared, expired }) };
}
test('Concurrent expired requests share one refresh and retry with the new token', async () => {
  const original = axios.post;
  let calls = 0;
  axios.post = async () => { calls++; await new Promise(resolve => setImmediate(resolve)); return { data: { access: 'fresh-access', refresh: 'rotated-refresh' } }; };
  try {
    const { client, current } = fixture();
    const results = await Promise.all([client.get('/rental-board/'), client.get('/rentals/')]);
    assert.equal(calls, 1); assert.equal(results.length, 2);
    assert.deepEqual(current(), { access: 'fresh-access', refresh: 'rotated-refresh', cleared: 0, expired: 0 });
  } finally { axios.post = original; }
});
test('A network failure during refresh preserves the saved session', async () => {
  const original = axios.post;
  axios.post = async () => { throw new axios.AxiosError('Offline', 'ERR_NETWORK'); };
  try {
    const { client, current } = fixture();
    await assert.rejects(client.get('/rentals/'));
    assert.equal(current().cleared, 0); assert.equal(current().expired, 0); assert.equal(current().refresh, 'old-refresh');
  } finally { axios.post = original; }
});
test('A rejected refresh clears the revoked session', async () => {
  const original = axios.post;
  axios.post = async () => { throw new axios.AxiosError('Revoked', 'ERR_BAD_REQUEST', {}, null, { status: 401 }); };
  try {
    const { client, current } = fixture();
    await assert.rejects(client.get('/rentals/'));
    assert.equal(current().cleared, 1); assert.equal(current().expired, 1);
  } finally { axios.post = original; }
});
test('Incorrect login credentials do not trigger token refresh', async () => {
  const original = axios.post; let calls = 0;
  axios.post = async () => { calls++; };
  try {
    const { client } = fixture();
    await assert.rejects(client.post('/auth/login/', { login: 'fixture' }));
    assert.equal(calls, 0);
  } finally { axios.post = original; }
});
