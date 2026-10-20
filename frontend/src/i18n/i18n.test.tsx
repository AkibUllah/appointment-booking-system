import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { LanguageToggle } from '@/components/LanguageToggle';
import { dictionaries } from './dict';
import { LanguageProvider, useLang } from './LanguageContext';

function Probe() {
  const { t, lang } = useLang();
  return <p data-testid="probe">{lang}:{t('nav_doctors')}</p>;
}

describe('i18n', () => {
  it('bn dictionary covers every en key', () => {
    const en = Object.keys(dictionaries.en).sort();
    const bn = Object.keys(dictionaries.bn).sort();
    expect(bn).toEqual(en);
    for (const key of en) {
      expect(dictionaries.bn[key as keyof typeof dictionaries.bn]).toBeTruthy();
    }
  });
  it('toggles labels between English and Bangla', () => {
    render(
      <LanguageProvider initial="en">
        <LanguageToggle />
        <Probe />
      </LanguageProvider>,
    );
    expect(screen.getByTestId('probe')).toHaveTextContent('en:Find a doctor');
    fireEvent.click(screen.getByRole('button', { name: 'বাং' }));
    expect(screen.getByTestId('probe')).toHaveTextContent('bn:ডাক্তার খুঁজুন');
    expect(screen.getByRole('button', { name: 'বাং' })).toHaveAttribute('aria-pressed', 'true');
  });
});
