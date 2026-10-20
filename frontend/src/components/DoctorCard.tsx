import { Link } from 'react-router-dom';
import type { Doctor } from '@/api/types';
import { useLang } from '@/i18n/LanguageContext';
import { formatBdt, toBanglaDigits } from '@/lib/format';

export function DoctorCard({ doctor }: { doctor: Doctor }) {
  const { t, lang } = useLang();
  const name = lang === 'bn' && doctor.name_bn ? doctor.name_bn : doctor.name;
  const specialty = lang === 'bn' && doctor.specialty.name_bn ? doctor.specialty.name_bn : doctor.specialty.name;
  const num = (n: number) => (lang === 'bn' ? toBanglaDigits(n) : String(n));
  return (
    <article className="card flex flex-col gap-3" data-testid="doctor-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-900">{name}</h3>
          <p className="text-sm text-slate-500">{doctor.degrees}</p>
        </div>
        <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700">{specialty}</span>
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-slate-600">
        <dt className="sr-only">Chamber</dt>
        <dd className="col-span-2">
          <span className="font-medium text-slate-800">{doctor.chamber.name}</span>
          <span className="text-slate-500"> · {doctor.chamber.area}</span>
        </dd>
        <dd>{t('fee')}: <span className="font-medium text-slate-900">{formatBdt(doctor.fee_bdt, lang)}</span></dd>
        <dd>{num(doctor.experience_years)} {t('years_exp')}</dd>
        <dd>{num(doctor.slot_minutes)} {t('slot_min')}</dd>
      </dl>
      <Link to={`/doctors/${doctor.id}`} className="btn-primary mt-auto self-start">
        {t('view_slots')}
      </Link>
    </article>
  );
}
