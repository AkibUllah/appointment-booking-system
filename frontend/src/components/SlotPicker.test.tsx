import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import type { DaySlots } from '@/api/types';
import { LanguageProvider } from '@/i18n/LanguageContext';
import { SlotPicker } from './SlotPicker';

const data: DaySlots[] = [
  {
    date: '2026-03-01',
    slots: [
      { start: '2026-03-01T17:00:00+06:00', end: '2026-03-01T17:15:00+06:00', available: true },
      { start: '2026-03-01T17:15:00+06:00', end: '2026-03-01T17:30:00+06:00', available: false },
    ],
  },
];

describe('SlotPicker', () => {
  it('renders dates, disables empty days and booked slots, and reports selection', async () => {
    const onSelectSlot = vi.fn();
    const onSelectDate = vi.fn();
    render(
      <LanguageProvider initial="en">
        <SlotPicker from="2026-03-01" days={2} data={data} selectedDate="2026-03-01" onSelectDate={onSelectDate} selectedSlot={null} onSelectSlot={onSelectSlot} />
      </LanguageProvider>,
    );
    const days = screen.getAllByRole('option');
    expect(days).toHaveLength(2);
    expect(days[1]).toBeDisabled();

    const booked = screen.getByRole('button', { name: '5:15 PM' });
    expect(booked).toBeDisabled();
    await userEvent.click(screen.getByRole('button', { name: '5:00 PM' }));
    expect(onSelectSlot).toHaveBeenCalledWith(data[0].slots[0]);
  });
});
