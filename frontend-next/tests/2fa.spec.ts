import { test, expect, request } from '@playwright/test';
import crypto from 'crypto';

function base32ToBytes(base32: string) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  const cleaned = base32.replace(/=+$/g, '').toUpperCase();
  const bytes = [] as number[];
  let bits = 0;
  let value = 0;
  for (const char of cleaned) {
    const idx = alphabet.indexOf(char);
    if (idx === -1) throw new Error('Invalid base32 char: ' + char);
    value = (value << 5) | idx;
    bits += 5;
    if (bits >= 8) {
      bits -= 8;
      bytes.push((value >> bits) & 0xff);
    }
  }
  return Uint8Array.from(bytes);
}

function totp(secret: string, digits = 6, interval = 30) {
  const key = base32ToBytes(secret);
  const epoch = Math.floor(Date.now() / 1000);
  const counter = Math.floor(epoch / interval);
  const buffer = Buffer.alloc(8);
  buffer.writeBigUInt64BE(BigInt(counter), 0);
  const hmac = crypto.createHmac('sha1', Buffer.from(key));
  hmac.update(buffer);
  const digest = hmac.digest();
  const offset = digest[digest.length - 1] & 0x0f;
  const code = ((digest.readUInt32BE(offset) & 0x7fffffff) % (10 ** digits)).toString();
  return code.padStart(digits, '0');
}

const API = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

test.describe('2FA E2E', () => {
  test('register -> setup -> enable -> login flows', async () => {
    const req = await request.newContext({ baseURL: API });

    const email = `playwright+${Date.now()}@example.com`;
    const password = 'Testpass123!';

    // Register
    const r1 = await req.post('/api/auth/register', { data: { email, password } });
    expect(r1.status()).toBe(201);

    // Login (dev auto-verify)
    const r2 = await req.post('/api/auth/login', { data: { email, password } });
    expect(r2.status()).toBe(200);
    const body2 = await r2.json();
    const token = body2.token || body2.data?.tokens?.accessToken;
    expect(token).toBeTruthy();

    const authHeaders = { Authorization: `Bearer ${token}` };

    // 2FA setup
    const r3 = await req.get('/api/profile/2fa/setup', { headers: authHeaders });
    expect(r3.status()).toBe(200);
    const setup = await r3.json();
    expect(setup.secret).toBeTruthy();

    const code = totp(setup.secret);

    // Enable 2FA
    const r4 = await req.post('/api/profile/2fa/enable', { headers: authHeaders, data: { otp: code } });
    expect(r4.status()).toBe(200);

    // Login without TOTP should require 2FA
    const r5 = await req.post('/api/auth/login', { data: { email, password } });
    expect(r5.status()).toBe(200);
    const b5 = await r5.json();
    expect(b5.requires_2fa).toBeTruthy();

    // Login with TOTP
    const totpCode = totp(setup.secret);
    const r6 = await req.post('/api/auth/login', { data: { email, password, totp_code: totpCode } });
    expect(r6.status()).toBe(200);
    const b6 = await r6.json();
    const token2 = b6.token || b6.data?.tokens?.accessToken;
    expect(token2).toBeTruthy();

    await req.dispose();
  });
});
