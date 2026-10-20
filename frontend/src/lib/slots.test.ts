import { describe, expect, it } from 'vitest';
import type { DaySlots } from '@/api/types';
import { availableCount, dateStrip, dhakaHour, groupSlots } from './slots';

const slot = (iso: string, available = true) => ({ start: iso, end: iso, available });

describe('slot helpers', () => {
  it('groups slots into morning / afternoon / evening by Dhaka hour', () => {
    const groups = groupSlots([
      slot('2026-03-01T09:00:00+06:00'),
      slot('2026-03-01T13:00:00+06:00'),
      slot('2026-03-01T17:00:00+06:00'),
      slot('2026-03-01T20:45:00+06:00'),
    ]);
    expect(groups.map((g) => [g.label, g.slots.length])).toEqual([['morning', 1], ['afternoon', 1], ['evening', 2]]);
  });
  it('omits empty groups', () => {
    expect(groupSlots([slot('2026-03-01T18:00:00+06:00')]).map((g) => g.label)).toEqual(['evening']);
  });
  it('reads the Dhaka hour from a UTC timestamp', () => {
    expect(dhakaHour('2026-03-01T11:00:00Z')).toBe(17);
  });
  it('counts only available slots', () => {
    const day: DaySlots = { date: '2026-03-01', slots: [slot('a'), slot('b', false)] };
    expect(availableCount(day)).toBe(1);
    expect(availableCount(undefined)).toBe(0);
  });
  it('builds a contiguous date strip including days without data', () => {
    const data: DaySlots[] = [{ date: '2026-03-01', slots: [slot('x'), slot('y', false)] }];
    const strip = dateStrip('2026-02-28', 3, data);
    expect(strip).toEqual([
      { date: '2026-02-28', available: 0 },
      { date: '2026-03-01', available: 1 },
      { date: '2026-03-02', available: 0 },
    ]);
  });
});
