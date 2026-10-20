import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState, type FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ApiRequestError, api } from '@/api/client';
import type { Booking, Slot } from '@/api/types';
import { SlotPicker } from '@/components/SlotPicker';
import { useToast } from '@/components/Toast';
import { SLOT_WINDOW_DAYS, useDoctorSlots } from '@/hooks/useDoctorSlots';
import { useLang } from '@/i18n/LanguageContext';
import { formatBdt, formatDateTime } from '@/lib/format';
import { isValidBdPhone } from '@/lib/phone';

export function DoctorPage() {
  const { id } = useParams();
  const doctorId = Number(id);
  const { t, lang } = useLang();
  const toast = useToast();
  const qc = useQueryClient();

  const doctor = useQuery({ queryKey: ['doctor', doctorId], queryFn: () => api.doctor(doctorId), enabled: Number.isFinite(doctorId) });
  const slots = useDoctorSlots(Number.isFinite(doctorId) ? doctorId : undefined);

  const [selectedDate, setSelectedDate] = useState<string>('');
  const [slot, setSlot] = useState<Slot | null>(null);
  const [phone, setPhone] = useState('');
  const [name, setName] = useState('');
  const [note, setNote] = useState('');
  const [confirmed, setConfirmed] = useState<Booking | null>(null);

  useEffect(() => {
    if (!selectedDate && slots.data) {
      const first = slots.data.find((d) => d.slots.some((s) => s.available));
      if (first) setSelectedDate(first.date);
    }
  }, [slots.data, selectedDate]);

  const book = useMutation({
    mutationFn: async () => {
      const patient = await api.registerPatient(phone, name.trim());
      return api.createBooking(doctorId, patient.id, slot!.start, note.trim() || undefined);
    },
    onSuccess: (b) => {
      setConfirmed(b);
      toast.push('success', t('booking_confirmed'));
      qc.invalidateQueries({ queryKey: ['slots', doctorId] });
    },
    onError: (err) => {
      toast.push('error', err instanceof ApiRequestError ? err.message : t('error_generic'));
      qc.invalidateQueries({ queryKey: ['slots', doctorId] });
      setSlot(null);
    },
  });

  const phoneOk = isValidBdPhone(phone);
  const canSubmit = !!slot && phoneOk && name.trim().length >= 2 && !book.isPending;

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (canSubmit) book.mutate();
  };

  if (doctor.isLoading) return <p className="text-sm text-slate-500">{t('loading')}</p>;
  if (doctor.isError || !doctor.data) return <p className="text-sm text-red-600">{t('error_generic')}</p>;
  const d = doctor.data;

  if (confirmed) {
    return (
      <div className="card mx-auto max-w-lg space-y-3">
        <h2 className="text-lg font-semibold text-brand-700">{t('booking_confirmed')}</h2>
        <p className="text-sm text-slate-600">{t('booking_ref')}: <span className="font-mono font-semibold">#{confirmed.id}</span></p>
        <p className="text-sm">{lang === 'bn' && d.name_bn ? d.name_bn : d.name} · {d.chamber.name}</p>
        <p className="text-sm font-medium">{formatDateTime(confirmed.slot_start, lang)}</p>
        <p className="text-xs text-slate-500">{t('policy_note')}</p>
        <Link to="/appointments" className="btn-secondary">{t('nav_appointments')}</Link>
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <section className="space-y-4 lg:col-span-2">
        <div className="card">
          <Link to="/" className="text-xs text-brand-700 hover:underline">← {t('back')}</Link>
          <h2 className="mt-1 text-xl font-semibold">{lang === 'bn' && d.name_bn ? d.name_bn : d.name}</h2>
          <p className="text-sm text-slate-500">{d.degrees} · {lang === 'bn' && d.specialty.name_bn ? d.specialty.name_bn : d.specialty.name}</p>
          <p className="mt-2 text-sm text-slate-700">{d.chamber.name}, {d.chamber.address}</p>
          <p className="text-sm text-slate-700">{t('fee')}: <span className="font-semibold">{formatBdt(d.fee_bdt, lang)}</span></p>
        </div>
        <div className="card">
          {slots.isLoading && <p className="text-sm text-slate-500">{t('loading')}</p>}
          {slots.data && (
            <SlotPicker
              from={slots.from}
              days={SLOT_WINDOW_DAYS}
              data={slots.data}
              selectedDate={selectedDate}
              onSelectDate={(dt) => { setSelectedDate(dt); setSlot(null); }}
              selectedSlot={slot?.start ?? null}
              onSelectSlot={setSlot}
            />
          )}
        </div>
      </section>
      <form onSubmit={submit} className="card space-y-3 self-start">
        <h3 className="font-semibold">{t('your_details')}</h3>
        {slot && <p className="rounded-md bg-brand-50 px-3 py-2 text-sm text-brand-700">{formatDateTime(slot.start, lang)}</p>}
        <div>
          <label className="label" htmlFor="phone">{t('phone')}</label>
          <input id="phone" className="input" inputMode="tel" placeholder="01712345678" value={phone} onChange={(e) => setPhone(e.target.value)} />
          {phone && !phoneOk && <p className="mt-1 text-xs text-red-600">{t('invalid_phone')}</p>}
        </div>
        <div>
          <label className="label" htmlFor="name">{t('name')}</label>
          <input id="name" className="input" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div>
          <label className="label" htmlFor="note">{t('note')}</label>
          <textarea id="note" className="input" rows={2} maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        <button type="submit" className="btn-primary w-full" disabled={!canSubmit}>{t('confirm_booking')}</button>
        <p className="text-xs text-slate-500">{t('policy_note')}</p>
      </form>
    </div>
  );
}
