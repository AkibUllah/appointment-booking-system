import { describe, expect, it } from 'vitest';
import { isValidBdPhone, normalizeBdPhone } from './phone';

describe('normalizeBdPhone', () => {
  it.each(['01712345678', '+8801712345678', '8801712345678', '017-1234-5678', ' 01712 345678 '])('normalises %s', (raw) => {
    expect(normalizeBdPhone(raw)).toBe('+8801712345678');
  });
  it.each(['0171234567', '01212345678', '+4401712345678', 'abc', ''])('rejects %s', (raw) => {
    expect(normalizeBdPhone(raw)).toBeNull();
    expect(isValidBdPhone(raw)).toBe(false);
  });
});
