import type { DaySlots, Slot } from '@/api/types';

export interface SlotGroup { label: 'morning' | 'afternoon' | 'evening'; slots: Slot[] }

/** Hour of the slot in Dhaka local time, derived from the ISO offset the API already applies. */
export function dhakaHour(iso: string): number {
  return Number(new Date(iso).toLocaleString('en-US', { hour: 'numeric', hour12: false, timeZone: 'Asia/Dhaka' }));
}

export function groupSlots(slots: Slot[]): SlotGroup[] {
  const groups: Record<SlotGroup['label'], Slot[]> = { morning: [], afternoon: [], evening: [] };
  for (const s of slots) {
    const h = dhakaHour(s.start);
    if (h < 12) groups.morning.push(s);
    else if (h < 17) groups.afternoon.push(s);
    else groups.evening.push(s);
  }
  return (Object.keys(groups) as SlotGroup['label'][])
    .filter((k) => groups[k].length > 0)
    .map((k) => ({ label: k, slots: groups[k] }));
}

export function availableCount(day: DaySlots | undefined): number {
  return day ? day.slots.filter((s) => s.available).length : 0;
}

/** Build a contiguous list of dates for the date strip; days without slots still appear (as disabled). */
export function dateStrip(from: string, days: number, data: DaySlots[]): { date: string; available: number }[] {
  const byDate = new Map(data.map((d) => [d.date, d]));
  const out: { date: string; available: number }[] = [];
  const [y, m, d] = from.split('-').map(Number);
  for (let i = 0; i < days; i++) {
    const iso = new Date(Date.UTC(y, m - 1, d + i)).toISOString().slice(0, 10);
    out.push({ date: iso, available: availableCount(byDate.get(iso)) });
  }
  return out;
}
