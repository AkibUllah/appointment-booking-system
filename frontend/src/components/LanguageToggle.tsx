import { useLang } from '@/i18n/LanguageContext';

export function LanguageToggle() {
  const { lang, setLang } = useLang();
  return (
    <div role="group" aria-label="Language" className="inline-flex overflow-hidden rounded-md border border-slate-300 text-xs font-medium">
      <button
        type="button"
        onClick={() => setLang('en')}
        aria-pressed={lang === 'en'}
        className={`px-3 py-1 ${lang === 'en' ? 'bg-brand-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-100'}`}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => setLang('bn')}
        aria-pressed={lang === 'bn'}
        className={`px-3 py-1 ${lang === 'bn' ? 'bg-brand-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-100'}`}
      >
        বাং
      </button>
    </div>
  );
}
