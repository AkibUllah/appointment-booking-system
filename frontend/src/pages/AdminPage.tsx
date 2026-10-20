import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { ApiRequestError, api } from '@/api/client';
import type { AvailabilityException, AvailabilityTemplate } from '@/api/types';
import { useToast } from '@/components/Toast';
import { useLang } from '@/i18n/LanguageContext';
import { toBanglaDigits } from '@/lib/format';

const hhmm = (t: string) => t.slice(0, 5);

export function AdminPage() {
  const { t, lang, weekdays } = useLang();
  const toast = useToast();
  const qc = useQueryClient();
  const onError = (err: unknown) => toast.push('error', err instanceof ApiRequestError ? err.message : t('error_generic'));

  const doctors = useQuery({ queryKey: ['doctors'], queryFn: () => api.doctors() });
  const stats = useQuery({ queryKey: ['admin-stats'], queryFn: api.admin.stats, retry: false });
  const [doctorId, setDoctorId] = useState<number | null>(null);
  useEffect(() => {
    if (doctorId === null && doctors.data?.length) setDoctorId(doctors.data[0].id);
  }, [doctors.data, doctorId]);

  const availability = useQuery({ queryKey: ['availability', doctorId], queryFn: () => api.admin.availability(doctorId!), enabled: doctorId !== null });
  const exceptions = useQuery({ queryKey: ['exceptions', doctorId], queryFn: () => api.admin.exceptions(doctorId!), enabled: doctorId !== null });

  const [rows, setRows] = useState<AvailabilityTemplate[]>([]);
  useEffect(() => { if (availability.data) setRows(availability.data.map((r) => ({ ...r }))); }, [availability.data]);

  const save = useMutation({
    mutationFn: () => api.admin.saveAvailability(doctorId!, rows.map((r) => ({ weekday: r.weekday, start_time: r.start_time, end_time: r.end_time }))),
    onSuccess: () => { toast.push('success', t('save')); qc.invalidateQueries({ queryKey: ['availability', doctorId] }); },
    onError,
  });

  const [exc, setExc] = useState<Omit<AvailabilityException, 'id'>>({ on_date: '', kind: 'leave', start_time: null, end_time: null, reason: '' });
  const [wholeDay, setWholeDay] = useState(true);
  const addExc = useMutation({
    mutationFn: () => api.admin.addException(doctorId!, { ...exc, start_time: wholeDay && exc.kind === 'leave' ? null : exc.start_time, end_time: wholeDay && exc.kind === 'leave' ? null : exc.end_time, reason: exc.reason || null }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['exceptions', doctorId] }); setExc({ on_date: '', kind: 'leave', start_time: null, end_time: null, reason: '' }); },
    onError,
  });
  const delExc = useMutation({
    mutationFn: (id: number) => api.admin.deleteException(doctorId!, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['exceptions', doctorId] }),
    onError,
  });

  const num = (n: number | string) => (lang === 'bn' ? toBanglaDigits(n) : String(n));

  return (
    <div className="space-y-6">
      <section className="grid gap-3 sm:grid-cols-4">
        {stats.isError && <p className="card text-sm text-red-600 sm:col-span-4">{(stats.error as Error).message}</p>}
        {stats.data && (
          <>
            <Stat label={t('total_bookings')} value={num(stats.data.total_bookings)} />
            <Stat label={t('today')} value={num(stats.data.today_confirmed)} />
            <Stat label={t('next_7_days')} value={num(stats.data.next_7_days_confirmed)} />
            <Stat label={t('cancellation_rate')} value={`${num(Math.round(stats.data.cancellation_rate * 100))}%`} />
          </>
        )}
      </section>

      <section className="card space-y-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="font-semibold">{t('weekly_schedule')}</h2>
          <select className="input sm:w-72" aria-label={t('select_doctor')} value={doctorId ?? ''} onChange={(e) => setDoctorId(Number(e.target.value))}>
            {(doctors.data ?? []).map((d) => <option key={d.id} value={d.id}>{d.name} · {d.chamber.area}</option>)}
          </select>
        </div>
        <table className="w-full text-sm">
          <thead className="text-left text-xs uppercase text-slate-500">
            <tr><th className="py-1">Day</th><th>Start</th><th>End</th><th></th></tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-t border-slate-100">
                <td className="py-2">
                  <select className="input" value={r.weekday} onChange={(e) => setRows(rows.map((x, j) => (j === i ? { ...x, weekday: Number(e.target.value) } : x)))}>
                    {weekdays.map((w, idx) => <option key={idx} value={idx}>{w}</option>)}
                  </select>
                </td>
                <td><input type="time" className="input" value={hhmm(r.start_time)} onChange={(e) => setRows(rows.map((x, j) => (j === i ? { ...x, start_time: e.target.value } : x)))} /></td>
                <td><input type="time" className="input" value={hhmm(r.end_time)} onChange={(e) => setRows(rows.map((x, j) => (j === i ? { ...x, end_time: e.target.value } : x)))} /></td>
                <td className="text-right"><button type="button" className="btn-danger" onClick={() => setRows(rows.filter((_, j) => j !== i))}>{t('remove')}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="flex gap-2">
          <button type="button" className="btn-secondary" onClick={() => setRows([...rows, { weekday: 6, start_time: '17:00', end_time: '21:00' }])}>{t('add_window')}</button>
          <button type="button" className="btn-primary" disabled={save.isPending || doctorId === null} onClick={() => save.mutate()}>{t('save')}</button>
        </div>
      </section>

      <section className="card space-y-4">
        <h2 className="font-semibold">{t('exceptions')}</h2>
        <div className="grid gap-2 md:grid-cols-6">
          <input type="date" className="input" value={exc.on_date} onChange={(e) => setExc({ ...exc, on_date: e.target.value })} aria-label="date" />
          <select className="input" value={exc.kind} onChange={(e) => setExc({ ...exc, kind: e.target.value as 'leave' | 'extra' })} aria-label="kind">
            <option value="leave">{t('leave')}</option>
            <option value="extra">{t('extra')}</option>
          </select>
          {exc.kind === 'leave' && (
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={wholeDay} onChange={(e) => setWholeDay(e.target.checked)} />{t('whole_day')}</label>
          )}
          {(exc.kind === 'extra' || !wholeDay) && (
            <>
              <input type="time" className="input" value={exc.start_time ?? ''} onChange={(e) => setExc({ ...exc, start_time: e.target.value })} aria-label="start" />
              <input type="time" className="input" value={exc.end_time ?? ''} onChange={(e) => setExc({ ...exc, end_time: e.target.value })} aria-label="end" />
            </>
          )}
          <input className="input" placeholder={t('reason')} value={exc.reason ?? ''} onChange={(e) => setExc({ ...exc, reason: e.target.value })} />
          <button type="button" className="btn-primary" disabled={!exc.on_date || addExc.isPending} onClick={() => addExc.mutate()}>{t('add')}</button>
        </div>
        <ul className="divide-y divide-slate-100 text-sm">
          {(exceptions.data ?? []).map((e) => (
            <li key={e.id} className="flex items-center justify-between py-2">
              <span>
                <span className="font-medium">{e.on_date}</span> · {e.kind === 'leave' ? t('leave') : t('extra')}
                {e.start_time ? ` ${hhmm(e.start_time)}–${hhmm(e.end_time ?? '')}` : ` (${t('whole_day')})`}
                {e.reason ? <span className="text-slate-500"> — {e.reason}</span> : null}
              </span>
              <button type="button" className="btn-danger" onClick={() => delExc.mutate(e.id!)}>{t('remove')}</button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}
