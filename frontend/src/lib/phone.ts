/** Mirrors the backend's Bangladeshi mobile number rules so users get instant feedback. */
const OPERATOR_PREFIXES = new Set(['13', '14', '15', '16', '17', '18', '19']);

export function normalizeBdPhone(raw: string): string | null {
  let digits = raw.replace(/[\s\-()]/g, '');
  if (digits.startsWith('+')) digits = digits.slice(1);
  if (digits.startsWith('880')) digits = digits.slice(3);
  if (digits.startsWith('0')) digits = digits.slice(1);
  if (!/^1\d{9}$/.test(digits)) return null;
  if (!OPERATOR_PREFIXES.has(digits.slice(0, 2))) return null;
  return `+880${digits}`;
}

export const isValidBdPhone = (raw: string): boolean => normalizeBdPhone(raw) !== null;
