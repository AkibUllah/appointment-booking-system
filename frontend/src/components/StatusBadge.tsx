import type { BookingStatus } from '@/api/types';
import { useLang } from '@/i18n/LanguageContext';

const styles: Record<BookingStatus, string> = {
  confirmed: 'bg-brand-50 text-brand-700',
  cancelled: 'bg-red-50 text-red-700',
  completed: 'bg-slate-100 text-slate-700',
  no_show: 'bg-amber-50 text-amber-700',
};

export function StatusBadge({ status }: { status: BookingStatus }) {
  const { t } = useLang();
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[status]}`}>{t(`status_${status}`)}</span>
  );
}
