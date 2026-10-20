import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { api } from '@/api/client';
import { DoctorCard } from '@/components/DoctorCard';
import { useLang } from '@/i18n/LanguageContext';

export function DoctorsPage() {
  const { t, lang } = useLang();
  const [params, setParams] = useSearchParams();
  const q = params.get('q') ?? '';
  const specialtyId = params.get('specialty') ?? '';
  const area = params.get('area') ?? '';
  const maxFee = params.get('max_fee') ?? '';

  const update = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  };

  const specialties = useQuery({ queryKey: ['specialties'], queryFn: api.specialties, staleTime: Infinity });
  const chambers = useQuery({ queryKey: ['chambers'], queryFn: api.chambers, staleTime: Infinity });
  const doctors = useQuery({
    queryKey: ['doctors', q, specialtyId, area, maxFee],
    queryFn: () =>
      api.doctors({
        q: q || undefined,
        specialty_id: specialtyId ? Number(specialtyId) : undefined,
        area: area || undefined,
        max_fee: maxFee ? Number(maxFee) : undefined,
      }),
  });
  const areas = Array.from(new Set((chambers.data ?? []).map((c) => c.area))).sort();

  return (
    <div className="space-y-6">
      <section className="card grid gap-3 md:grid-cols-4">
        <input
          className="input md:col-span-2"
          placeholder={t('search_placeholder')}
          value={q}
          onChange={(e) => update('q', e.target.value)}
          aria-label={t('search_placeholder')}
        />
        <select className="input" value={specialtyId} onChange={(e) => update('specialty', e.target.value)} aria-label={t('all_specialties')}>
          <option value="">{t('all_specialties')}</option>
          {(specialties.data ?? []).map((s) => (
            <option key={s.id} value={s.id}>{lang === 'bn' && s.name_bn ? s.name_bn : s.name}</option>
          ))}
        </select>
        <select className="input" value={area} onChange={(e) => update('area', e.target.value)} aria-label={t('all_areas')}>
          <option value="">{t('all_areas')}</option>
          {areas.map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
        <label className="flex items-center gap-3 text-sm text-slate-600 md:col-span-4">
          <span className="w-24">{t('max_fee')}</span>
          <input type="range" min={300} max={2000} step={100} value={maxFee || 2000} onChange={(e) => update('max_fee', e.target.value === '2000' ? '' : e.target.value)} className="flex-1" />
          <span className="w-20 text-right font-medium">৳{maxFee || '2,000'}</span>
        </label>
      </section>

      {doctors.isLoading && <p className="text-sm text-slate-500">{t('loading')}</p>}
      {doctors.isError && <p className="text-sm text-red-600">{(doctors.error as Error).message}</p>}
      {doctors.data && doctors.data.length === 0 && <p className="text-sm text-slate-500">{t('no_doctors')}</p>}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {(doctors.data ?? []).map((d) => <DoctorCard key={d.id} doctor={d} />)}
      </section>
    </div>
  );
}
