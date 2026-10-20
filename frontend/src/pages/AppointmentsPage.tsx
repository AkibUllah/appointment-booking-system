import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState, type FormEvent } from 'react';
import { ApiRequestError, api } from '@/api/client';
import type { Booking, Slot } from '@/api/types';
import { SlotPicker } from '@/components/SlotPicker';
import { StatusBadge } from '@/components/StatusBadge';
import { useToast } from '@/components/Toast';
import { SLOT_WINDOW_DAYS, useDoctorSlots } from '@/hooks/useDoctorSlots';
import { useLang } from '@/i18n/LanguageContext';
import { formatDateTime } from '@/lib/format';
import { isValidBdPhone } from '@/lib/phone';

const PHONE_KEY = 'booking.phone';

function RescheduleDialog({ booking, onClose }: { booking: Booking; onClose: () => void }) {
  const { t, lang } = useLang();
  const toast = useToast();
  const qc = useQueryClient();
  const slots = useDoctorSlots(booking.doctor.id);
  const [date, setDate] = useState('');
  const [slot, setSlot] = useState<Slot | null>(null);
  useEffect(() => {
    if (!date && slots.data) {
      const first = slots.data.find((d) => d.slots.some((s) => s.available));
      if (first) setDate(first.date);
    }
  }, [slots.data, date]);
  const move = useMutation({
    mutationFn: () => api.rescheduleBooking(booking.id, booking.version, slot!.start),
    onSuccess: () => {
      toast.push('success', `${t('reschedule')}: ${formatDateTime(slot!.start, lang)}`);
      qc.invalidateQueries({ queryKey: ['my-bookings'] });
      onClose();
    },
    onError: (err) => toast.push('error', err instanceof ApiRequestError ? err.message : t('error_generic')),
  });
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/40 p-4" role="dialog" aria-modal="true">
      <div className="card max-h-[90vh] w-full max-w-2xl overflow-y-auto space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{t('choose_new_slot')} · {booking.doctor.name}</h3>
          <button type="button" className="btn-secondary" onClick={onClose}>{t('back')}</button>
        </div>
        {slots.data && (
          <SlotPicker from={slots.from} days={SLOT_WINDOW_DAYS} data={slots.data} selectedDate={date} onSelectDate={(d) => { setDate(d); setSlot(null); }} selectedSlot={slot?.start ?? null} onSelectSlot={setSlot} />
        )}
        <button type="button" className="btn-primary" disabled={!slot || move.isPending} onClick={() => move.mutate()}>{t('reschedule')}</button>
      </div>
    </div>
  );
}

export function AppointmentsPage() {
  const { t, lang } = useLang();
  const toast = useToast();
  const qc = useQueryClient();
  const [input, setInput] = useState(() => { try { return localStorage.getItem(PHONE_KEY) ?? ''; } catch { return ''; } });
  const [phone, setPhone] = useState(() => (isValidBdPhone(input) ? input : ''));
  const [rescheduling, setRescheduling] = useState<Booking | null>(null);

  const bookings = useQuery({ queryKey: ['my-bookings', phone], queryFn: () => api.bookingsByPhone(phone), enabled: !!phone });

  const cancel = useMutation({
    mutationFn: (b: Booking) => api.cancelBooking(b.id, b.version),
    onSuccess: () => { toast.push('success', t('status_cancelled')); qc.invalidateQueries({ queryKey: ['my-bookings'] }); },
    onError: (err) => { toast.push('error', err instanceof ApiRequestError ? err.message : t('error_generic')); qc.invalidateQueries({ queryKey: ['my-bookings'] }); },
  });

  const lookup = (e: FormEvent) => {
    e.preventDefault();
    if (!isValidBdPhone(input)) return;
    try { localStorage.setItem(PHONE_KEY, input); } catch { /* ignore */ }
    setPhone(input);
  };

  const upcoming = (b: Booking) => b.status === 'confirmed' && new Date(b.slot_start).getTime() > Date.now();

  return (
    <div className="space-y-6">
      <form onSubmit={lookup} className="card flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label className="label" htmlFor="lookup-phone">{t('lookup_phone')}</label>
          <input id="lookup-phone" className="input" inputMode="tel" placeholder="01712345678" value={input} onChange={(e) => setInput(e.target.value)} />
        </div>
        <button type="submit" className="btn-primary" disabled={!isValidBdPhone(input)}>{t('lookup')}</button>
      </form>
      {bookings.isLoading && <p className="text-sm text-slate-500">{t('loading')}</p>}
      {bookings.data && bookings.data.length === 0 && <p className="text-sm text-slate-500">{t('no_appointments')}</p>}
      <ul className="space-y-3">
        {(bookings.data ?? []).map((b) => (
          <li key={b.id} className="card flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-slate-400">#{b.id}</span>
                <StatusBadge status={b.status} />
              </div>
              <p className="mt-1 font-medium">{lang === 'bn' && b.doctor.name_bn ? b.doctor.name_bn : b.doctor.name}</p>
              <p className="text-sm text-slate-600">{b.chamber.name} · {b.chamber.area}</p>
              <p className="text-sm font-medium text-slate-800">{formatDateTime(b.slot_start, lang)}</p>
            </div>
            {upcoming(b) && (
              <div className="flex gap-2">
                <button type="button" className="btn-secondary" onClick={() => setRescheduling(b)}>{t('reschedule')}</button>
                <button type="button" className="btn-danger" onClick={() => cancel.mutate(b)} disabled={cancel.isPending}>{t('cancel')}</button>
              </div>
            )}
          </li>
        ))}
      </ul>
      {rescheduling && <RescheduleDialog booking={rescheduling} onClose={() => setRescheduling(null)} />}
    </div>
  );
}
