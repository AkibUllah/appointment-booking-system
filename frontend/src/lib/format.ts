import type { Lang } from '@/i18n/dict';

const BN_DIGITS = ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯'];

export function toBanglaDigits(input: string | number): string {
  return String(input).replace(/\d/g, (d) => BN_DIGITS[Number(d)]);
}

/** BDT with the ৳ sign, lakh/crore grouping is not needed for chamber fees so plain grouping is used. */
export function formatBdt(amount: number, lang: Lang = 'en'): string {
  const grouped = amount.toLocaleString('en-US');
  return `৳${lang === 'bn' ? toBanglaDigits(grouped) : grouped}`;
}

const DHAKA_TZ = 'Asia/Dhaka';

export function formatTime(iso: string, lang: Lang = 'en'): string {
  const s = new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: DHAKA_TZ });
  return lang === 'bn' ? toBanglaDigits(s) : s;
}

export function formatDate(iso: string, lang: Lang = 'en'): string {
  const d = new Date(iso);
  const s = d.toLocaleDateString(lang === 'bn' ? 'bn-BD' : 'en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: DHAKA_TZ,
  });
  return s;
}

export function formatDateTime(iso: string, lang: Lang = 'en'): string {
  return `${formatDate(iso, lang)}, ${formatTime(iso, lang)}`;
}

/** YYYY-MM-DD for a Date, in the Dhaka calendar. */
export function isoDateInDhaka(d: Date): string {
  const parts = new Intl.DateTimeFormat('en-CA', { timeZone: DHAKA_TZ, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(d);
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? '';
  return `${get('year')}-${get('month')}-${get('day')}`;
}

export function addDays(isoDate: string, days: number): string {
  const [y, m, d] = isoDate.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d + days));
  return dt.toISOString().slice(0, 10);
}
