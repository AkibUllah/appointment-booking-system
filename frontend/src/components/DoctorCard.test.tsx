import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import type { Doctor } from '@/api/types';
import { LanguageProvider } from '@/i18n/LanguageContext';
import { DoctorCard } from './DoctorCard';

const doctor: Doctor = {
  id: 7,
  name: 'Dr. Farhana Rahman',
  name_bn: 'ডা. ফারহানা রহমান',
  degrees: 'MBBS, MD (Cardiology)',
  specialty: { id: 1, name: 'Cardiology', name_bn: 'হৃদরোগ' },
  chamber: { id: 1, name: 'Sunflower Dhanmondi', area: 'Dhanmondi', address: 'Road 4', phone: null },
  slot_minutes: 15,
  fee_bdt: 1200,
  experience_years: 14,
  is_active: true,
};

describe('DoctorCard', () => {
  it('shows English details and links to the slot page', () => {
    render(
      <MemoryRouter>
        <LanguageProvider initial="en"><DoctorCard doctor={doctor} /></LanguageProvider>
      </MemoryRouter>,
    );
    expect(screen.getByText('Dr. Farhana Rahman')).toBeInTheDocument();
    expect(screen.getByText('৳1,200')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'View slots' })).toHaveAttribute('href', '/doctors/7');
  });
  it('switches to Bangla name, specialty and numerals', () => {
    render(
      <MemoryRouter>
        <LanguageProvider initial="bn"><DoctorCard doctor={doctor} /></LanguageProvider>
      </MemoryRouter>,
    );
    expect(screen.getByText('ডা. ফারহানা রহমান')).toBeInTheDocument();
    expect(screen.getByText('হৃদরোগ')).toBeInTheDocument();
    expect(screen.getByText('৳১,২০০')).toBeInTheDocument();
  });
});
