import { NavLink, Outlet } from 'react-router-dom';
import { useLang } from '@/i18n/LanguageContext';
import { LanguageToggle } from './LanguageToggle';
import { ToastViewport } from './Toast';

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-2 text-sm font-medium ${isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100'}`;

export function Layout() {
  const { t } = useLang();
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <NavLink to="/" className="flex items-center gap-2 text-lg font-semibold text-brand-700">
            <svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true">
              <rect width="32" height="32" rx="7" fill="#0f8a6a" />
              <path d="M9 16h14M16 9v14" stroke="#fff" strokeWidth="4" strokeLinecap="round" />
            </svg>
            {t('appName')}
          </NavLink>
          <nav className="hidden items-center gap-1 sm:flex">
            <NavLink to="/" end className={linkClass}>{t('nav_doctors')}</NavLink>
            <NavLink to="/appointments" className={linkClass}>{t('nav_appointments')}</NavLink>
            <NavLink to="/admin" className={linkClass}>{t('nav_admin')}</NavLink>
          </nav>
          <LanguageToggle />
        </div>
        <nav className="flex gap-1 overflow-x-auto px-4 pb-2 sm:hidden">
          <NavLink to="/" end className={linkClass}>{t('nav_doctors')}</NavLink>
          <NavLink to="/appointments" className={linkClass}>{t('nav_appointments')}</NavLink>
          <NavLink to="/admin" className={linkClass}>{t('nav_admin')}</NavLink>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
      <ToastViewport />
    </div>
  );
}
