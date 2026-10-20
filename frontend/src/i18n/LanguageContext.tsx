import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import { dictionaries, type DictKey, type Lang } from './dict';

interface LanguageValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: DictKey) => string;
  weekdays: readonly string[];
}

const LanguageContext = createContext<LanguageValue | null>(null);
const STORAGE_KEY = 'booking.lang';

function readStored(): Lang {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return v === 'bn' ? 'bn' : 'en';
  } catch {
    return 'en';
  }
}

export function LanguageProvider({ children, initial }: { children: ReactNode; initial?: Lang }) {
  const [lang, setLangState] = useState<Lang>(initial ?? readStored());
  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try {
      localStorage.setItem(STORAGE_KEY, l);
    } catch {
      /* storage unavailable: language just won't persist */
    }
  }, []);
  const value = useMemo<LanguageValue>(() => {
    const dict = dictionaries[lang];
    return {
      lang,
      setLang,
      t: (key) => {
        const v = dict[key];
        return typeof v === 'string' ? v : String(dictionaries.en[key]);
      },
      weekdays: dict.weekdays as readonly string[],
    };
  }, [lang, setLang]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLang(): LanguageValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLang must be used inside LanguageProvider');
  return ctx;
}
