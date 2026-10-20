import { describe, expect, it } from 'vitest';
import { addDays, formatBdt, formatTime, isoDateInDhaka, toBanglaDigits } from './format';

describe('format helpers', () => {
  it('converts digits to Bangla numerals', () => {
    expect(toBanglaDigits(1200)).toBe('১২০০');
    expect(toBanglaDigits('2026-03-01')).toBe('২০২৬-০৩-০১');
  });
  it('formats BDT in both languages', () => {
    expect(formatBdt(1200)).toBe('৳1,200');
    expect(formatBdt(1200, 'bn')).toBe('৳১,২০০');
  });
  it('renders times in Dhaka local time regardless of host zone', () => {
    expect(formatTime('2026-03-01T11:00:00Z')).toBe('5:00 PM');
    expect(formatTime('2026-03-01T11:00:00+06:00')).toBe('11:00 AM');
  });
  it('derives the Dhaka calendar date', () => {
    // 20:30 UTC is already the next day in Dhaka (+6)
    expect(isoDateInDhaka(new Date('2026-03-01T20:30:00Z'))).toBe('2026-03-02');
    expect(isoDateInDhaka(new Date('2026-03-01T17:30:00Z'))).toBe('2026-03-01');
  });
  it('adds days across month boundaries', () => {
    expect(addDays('2026-02-27', 3)).toBe('2026-03-02');
    expect(addDays('2026-12-31', 1)).toBe('2027-01-01');
  });
});
