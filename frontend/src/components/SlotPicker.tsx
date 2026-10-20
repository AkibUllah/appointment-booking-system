import type { DaySlots, Slot } from '@/api/types';
import { useLang } from '@/i18n/LanguageContext';
import { formatTime, toBanglaDigits } from '@/lib/format';
import { dateStrip, groupSlots } from '@/lib/slots';

interface Props {
  from: string;
  days: number;
  data: DaySlots[];
  selectedDate: string;
  onSelectDate: (d: string) => void;
  selectedSlot: string | null;
  onSelectSlot: (s: Slot) => void;
}

const groupLabels = {
  en: { morning: 'Morning', afternoon: 'Afternoon', evening: 'Evening' },
  bn: { morning: 'সকাল', afternoon: 'বিকাল', evening: 'সন্ধ্যা' },
} as const;

export function SlotPicker({ from, days, data, selectedDate, onSelectDate, selectedSlot, onSelectSlot }: Props) {
  const { t, lang, weekdays } = useLang();
  const strip = dateStrip(from, days, data);
  const day = data.find((d) => d.date === selectedDate);
  const groups = day ? groupSlots(day.slots) : [];

  return (
    <div className="space-y-4">
      <div>
        <p className="label">{t('pick_date')}</p>
        <div className="flex gap-2 overflow-x-auto pb-1" role="listbox" aria-label={t('pick_date')}>
          {strip.map(({ date, available }) => {
            const [y, m, d] = date.split('-').map(Number);
            const weekday = new Date(Date.UTC(y, m - 1, d)).getUTCDay(); // 0=Sun
            const label = weekdays[(weekday + 6) % 7];
            const active = date === selectedDate;
            return (
              <button
                key={date}
                type="button"
                role="option"
                aria-selected={active}
                disabled={available === 0}
                onClick={() => onSelectDate(date)}
                className={`flex min-w-[64px] flex-col items-center rounded-md border px-2 py-2 text-xs ${
                  active ? 'border-brand-600 bg-brand-600 text-white' : 'border-slate-200 bg-white text-slate-700 hover:border-brand-500'
                } disabled:opacity-40`}
              >
                <span className="font-medium">{label}</span>
                <span className="text-base font-semibold">{lang === 'bn' ? toBanglaDigits(d) : d}</span>
                <span className={active ? 'text-brand-100' : 'text-slate-400'}>
                  {lang === 'bn' ? toBanglaDigits(available) : available}
                </span>
              </button>
            );
          })}
        </div>
      </div>
      <div>
        <p className="label">{t('pick_slot')}</p>
        {groups.length === 0 && <p className="text-sm text-slate-500">{t('no_slots')}</p>}
        {groups.map((g) => (
          <div key={g.label} className="mb-3">
            <p className="mb-1 text-xs font-medium text-slate-500">{groupLabels[lang][g.label]}</p>
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-6">
              {g.slots.map((s) => {
                const active = s.start === selectedSlot;
                return (
                  <button
                    key={s.start}
                    type="button"
                    disabled={!s.available}
                    onClick={() => onSelectSlot(s)}
                    title={s.available ? undefined : t('booked')}
                    className={`rounded-md border px-2 py-1.5 text-sm ${
                      active
                        ? 'border-brand-600 bg-brand-600 text-white'
                        : s.available
                          ? 'border-slate-200 bg-white hover:border-brand-500'
                          : 'border-slate-100 bg-slate-100 text-slate-400 line-through'
                    }`}
                  >
                    {formatTime(s.start, lang)}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
